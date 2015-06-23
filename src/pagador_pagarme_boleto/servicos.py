# -*- coding: utf-8 -*-

import json
from time import sleep
from pagador import servicos


# import logging
# logger = logging.getLogger('PAGARME-BOLETO')

TEMPO_MAXIMO_ESPERA_NOTIFICACAO = 30



class Ambiente(object):
    test = 'T'
    live = 'L'


class Credenciador(servicos.Credenciador):
    def __init__(self, tipo=None, configuracao=None):
        super(Credenciador, self).__init__(tipo, configuracao)
        self.tipo = self.TipoAutenticacao.query_string
        self.chave_api = str(getattr(self.configuracao, 'token', ''))
        self.chave = 'api_key'

    def obter_credenciais(self):
        return self.chave_api


MENSAGEM_DADOS_INVALIDOS = {
    'customer[phone][ddd]': u'O DDD do seu número de telefone está faltando ou é inválido.',
    'customer[phone][number]': u'O seu número de telefone está faltando ou é inválido.',
    'customer[address][zipcode]': u'O seu CEP está faltando ou é inválido.',
}


MENSAGENS_RETORNO = {
    'processing': 'Pagamento sendo processado',
    'authorized': 'Pagamento autorizado',
    'paid': 'Pagamento aprovado',
    'refused': 'Pagamento recusado',
    'waiting_payment': 'Aguardando pagamento',
    'pending_refund': 'Pagamento em disputa',
    'refunded': 'Pagamento retornado'
}


class EntregaPagamento(servicos.EntregaPagamento):
    def __init__(self, loja_id, plano_indice=1, dados=None):
        super(EntregaPagamento, self).__init__(loja_id, plano_indice, dados=dados)
        self.tem_malote = True
        self.faz_http = True
        self.conexao = self.obter_conexao()
        self.url = 'https://api.pagar.me/1/transactions'
        self.dados_pagamento = {}

    def define_credenciais(self):
        self.conexao.credenciador = Credenciador(configuracao=self.configuracao)

    def envia_pagamento(self, tentativa=1):
        if self.pedido.situacao_id and self.pedido.situacao_id != servicos.SituacaoPedido.SITUACAO_PEDIDO_EFETUADO:
            self.resultado = {
                'sucesso': self.pedido.situacao_id == servicos.SituacaoPedido.SITUACAO_PEDIDO_PAGO,
                'situacao_pedido': self.situacao_pedido,
                'alterado_por_notificacao': False
            }
            next_url = self.dados.get('next_url', None)
            if next_url:
                self.resultado['next_url'] = next_url
            raise self.PedidoJaRealizado(u'Esse pedido já foi realizado e está com status {}'.format(self.pedido.situacao_id))
        self.dados_enviados = self.malote.to_dict()
        self.resposta = self.conexao.post(self.url, self.dados_enviados)

    def _verifica_erro_em_conteudo(self, titulo):
        mensagens = []
        titulo_substituto = []
        invalid_parameter = False
        if 'conteudo_json' not in self.dados_pagamento:
            self.dados_pagamento['conteudo_json'] = {'mensagem_retorno': ''}
        if self.resposta.conteudo:
            erros = self.resposta.conteudo.get('errors', None)
            if erros:
                for erro in erros:
                    if erro['type'] == 'invalid_parameter':
                        invalid_parameter = True
                        mensagens.append(u'{}: {}'.format(erro['parameter_name'], erro['message']))
                        titulo_substituto.append(MENSAGEM_DADOS_INVALIDOS.get(erro['parameter_name'], erro['message']))
                    elif erro['type'] == 'action_forbidden' and 'refused' in erro['message']:
                        return False
                    elif erro['type'] == 'action_forbidden' and 'processing' in erro['message']:
                        return True
                    else:
                        mensagens.append(erro['message'])
            else:
                mensagens.append(json.dumps(self.resposta.conteudo))
        if invalid_parameter:
            titulo = u'\nDados inválidos:\n{}'.format('\n'.join(titulo_substituto))
        mensagens.append(u'HTTP STATUS CODE: {}'.format(self.resposta.status_code))
        self.dados_pagamento['conteudo_json']['mensagem_retorno'] = titulo
        raise self.EnvioNaoRealizado(
            titulo,
            self.loja_id,
            self.pedido.numero,
            dados_envio=self.dados_enviados,
            erros=mensagens,
            status=(400 if invalid_parameter else 500)
        )

    def processa_dados_pagamento(self):
        if self.resposta.sucesso:
            self.dados_pagamento = {
                'transacao_id': self.resposta.conteudo['id'],
                'valor_pago': self.formatador.formata_decimal(self.pedido.valor_total),
                'conteudo_json': {
                    'aplicacao': self.configuracao.aplicacao,
                    'boleto_url': self.resposta.conteudo['boleto_url'],
                    'codigo_barras': self.resposta.conteudo['boleto_barcode'],
                    'vencimento': self.resposta.conteudo['boleto_expiration_date'],
                }
            }
            # logger.debug('\n\n\nRECEBIDO:\n{}\n\n\n'.format(self.resposta.conteudo))
            # logger.debug('\n\n\nENVIADO:\n{}\n\n\n'.format(self.dados_enviados))
            self.identificacao_pagamento = self.resposta.conteudo['id']
            self.situacao_pedido = SituacoesDePagamento.do_tipo(self.resposta.conteudo['status'])
            self.resultado = {'boleto_url': self.resposta.conteudo['boleto_url'], 'sucesso': self.resposta.conteudo['status'] == 'waiting_payment', 'situacao_pedido': self.situacao_pedido, 'alterado_por_notificacao': False}
        elif self.resposta.requisicao_invalida or self.resposta.nao_autorizado:
            self.situacao_pedido = SituacoesDePagamento.do_tipo('refused')
            titulo = u'A autenticação da loja com o PAGAR.ME falhou. Por favor, entre em contato com nosso SAC.' if self.resposta.nao_autorizado else u'Ocorreu um erro nos dados enviados ao PAGAR.ME. Por favor, entre em contato com nosso SAC.'
            if not self._verifica_erro_em_conteudo(titulo):
                self.resultado = {'sucesso': False, 'mensagem': u'nao_aprovado', 'situacao_pedido': self.situacao_pedido, 'fatal': True}
        else:
            self.situacao_pedido = SituacoesDePagamento.do_tipo('refused')
            self._verifica_erro_em_conteudo(u'Não foi obtida uma resposta válida do PAGAR.ME. Nosso equipe técnica está avaliando o problema.')


class SituacoesDePagamento(servicos.SituacoesDePagamento):
    DE_PARA = {
        'processing': servicos.SituacaoPedido.SITUACAO_PAGTO_EM_ANALISE,
        'authorized': servicos.SituacaoPedido.SITUACAO_PAGTO_EM_ANALISE,
        'paid': servicos.SituacaoPedido.SITUACAO_PEDIDO_PAGO,
        'refused': servicos.SituacaoPedido.SITUACAO_PEDIDO_CANCELADO,
        'waiting_payment': servicos.SituacaoPedido.SITUACAO_AGUARDANDO_PAGTO,
        'pending_refund': servicos.SituacaoPedido.SITUACAO_PAGTO_EM_DISPUTA,
        'refunded': servicos.SituacaoPedido.SITUACAO_PAGTO_DEVOLVIDO
    }


class RegistraNotificacao(servicos.RegistraResultado):
    def __init__(self, loja_id, dados=None):
        super(RegistraNotificacao, self).__init__(loja_id, dados)

    @property
    def transacao_id(self):
        return self.dados.get('id', None)

    @property
    def pedido_id(self):
        return self.dados.get('referencia', None)

    @property
    def status(self):
        return self.dados.get('current_status', None)

    def monta_dados_pagamento(self):
        self.pedido_numero = self.pedido_id
        self.situacao_pedido = SituacoesDePagamento.do_tipo(self.status)
        self.resultado = {'resultado': 'OK'}
