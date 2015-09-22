# -*- coding: utf-8 -*-
from decimal import Decimal
import unittest
import mock
from pagador_pagarme_boleto import servicos


class PagarMeBoletoCredenciais(unittest.TestCase):
    def test_deve_definir_propriedades(self):
        credenciador = servicos.Credenciador(configuracao=mock.MagicMock())
        credenciador.tipo.should.be.equal(credenciador.TipoAutenticacao.query_string)
        credenciador.chave.should.be.equal('api_key')

    def test_deve_retornar_credencial_baseado_no_usuario(self):
        configuracao = mock.MagicMock(token='api-key')
        credenciador = servicos.Credenciador(configuracao=configuracao)
        credenciador.obter_credenciais().should.be.equal('api-key')


class PagarMeBoletoSituacoesPagamento(unittest.TestCase):
    def test_deve_retornar_pago_para_paid(self):
        servicos.SituacoesDePagamento.do_tipo('paid').should.be.equal(servicos.servicos.SituacaoPedido.SITUACAO_PEDIDO_PAGO)

    def test_deve_retornar_cancelado_para_refused(self):
        servicos.SituacoesDePagamento.do_tipo('refused').should.be.equal(servicos.servicos.SituacaoPedido.SITUACAO_PEDIDO_CANCELADO)

    def test_deve_retornar_none_para_desconhecido(self):
        servicos.SituacoesDePagamento.do_tipo('zas').should.be.none


class PagarMeBoletoEntregaPagamento(unittest.TestCase):
    def setUp(self):
        self.conexao_mock = mock.MagicMock()
        with mock.patch('pagador_pagarme_boleto.servicos.EntregaPagamento.obter_conexao') as obter_mock:
            obter_mock.return_value = self.conexao_mock
            self.entregador = servicos.EntregaPagamento(8)
            self.entregador.pedido = mock.MagicMock(
                valor_total=Decimal('123.56'),
                numero=1234,
                situacao_id=servicos.servicos.SituacaoPedido.SITUACAO_PEDIDO_EFETUADO
            )
            self.entregador.dados = {}
            self.entregador.configuracao = mock.MagicMock(aplicacao='test')

    @mock.patch('pagador_pagarme_boleto.servicos.EntregaPagamento.obter_conexao', mock.MagicMock())
    def test_deve_dizer_que_tem_malote(self):
        self.entregador.tem_malote.should.be.truthy

    @mock.patch('pagador_pagarme_boleto.servicos.EntregaPagamento.obter_conexao', mock.MagicMock())
    def test_deve_dizer_que_faz_http(self):
        self.entregador.faz_http.should.be.truthy

    @mock.patch('pagador_pagarme_boleto.servicos.EntregaPagamento.obter_conexao', mock.MagicMock())
    def test_deve_definir_url(self):
        self.entregador.url.should.be.equal('https://api.pagar.me/1/transactions')

    def test_deve_montar_conexao(self):
        self.entregador.conexao.should.be.equal(self.conexao_mock)

    @mock.patch('pagador_pagarme_boleto.servicos.EntregaPagamento.obter_conexao', mock.MagicMock())
    @mock.patch('pagador_pagarme_boleto.servicos.Credenciador')
    def test_deve_definir_credenciais(self, credenciador_mock):
        credenciador_mock.return_value = 'credenciador'
        self.entregador.configuracao = 'configuracao'
        self.entregador.define_credenciais()
        self.entregador.conexao.credenciador.should.be.equal('credenciador')
        credenciador_mock.assert_called_with(configuracao='configuracao')

    @mock.patch('pagador_pagarme_boleto.servicos.EntregaPagamento.obter_conexao', mock.MagicMock())
    def test_deve_enviar_pagamento(self):
        self.entregador.malote = mock.MagicMock()
        self.entregador.malote.to_dict.return_value = 'malote-como-dicionario'
        self.entregador.conexao = mock.MagicMock()
        self.entregador.conexao.post.return_value = 'resposta'
        self.entregador.envia_pagamento()
        self.entregador.dados_enviados.should.be.equal('malote-como-dicionario')
        self.entregador.resposta.should.be.equal('resposta')

    @mock.patch('pagador_pagarme_boleto.servicos.EntregaPagamento.obter_conexao', mock.MagicMock())
    def test_deve_usar_post_ao_enviar_pagamento(self):
        self.entregador.malote = mock.MagicMock()
        self.entregador.malote.to_dict.return_value = 'malote-como-dicionario'
        self.entregador.conexao = mock.MagicMock()
        self.entregador.envia_pagamento()
        self.entregador.conexao.post.assert_called_with(self.entregador.url, 'malote-como-dicionario')


    # def test_processa_pagamento_boleto(self):
    #     self.entregador.configuracao = mock.MagicMock(aplicacao='test')
    #     self.entregador.pedido.conteudo_json['pagarme']['metodo'] = 'boleto'
    #     self.entregador.resposta = mock.MagicMock(sucesso=True, requisicao_invalida=False, conteudo={'status': 'waiting_payment', 'id': 'identificacao-id', 'boleto_url': 'url-boleto', 'boleto_barcode': 'codigo-barras-boleto', 'boleto_expiration_date': 'data-expiracao-boleto'})
    #     self.entregador.processa_dados_pagamento()
    #     self.entregador.dados_pagamento.should.be.equal({'conteudo_json': {'metodo': 'boleto', 'aplicacao': 'test', 'boleto_url': 'url-boleto', 'codigo_barras': 'codigo-barras-boleto', 'vencimento': 'data-expiracao-boleto'}, 'transacao_id': 'identificacao-id', 'valor_pago': '123.56'})
    #
    # def test_processa_pagamento_boleto_sem_sucesso(self):
    #     self.entregador.configuracao = mock.MagicMock(aplicacao='test')
    #     self.entregador.pedido.conteudo_json['pagarme']['metodo'] = 'boleto'
    #     self.entregador.resposta = mock.MagicMock(sucesso=True, requisicao_invalida=False, conteudo={'status': 'refused'})
    #     self.entregador.processa_dados_pagamento()
    #     self.entregador.dados_pagamento.should.be.empty

    @mock.patch('pagador_pagarme_boleto.servicos.EntregaPagamento.obter_conexao', mock.MagicMock())
    def test_processar_dados_de_pagamento_define_dados_pagamento(self):
        self.entregador.configuracao = mock.MagicMock(aplicacao='test')
        self.entregador.resposta = mock.MagicMock(sucesso=True, requisicao_invalida=False, conteudo={'status': 'waiting_payment', 'id': 'identificacao-id', 'boleto_url': 'url-boleto', 'boleto_barcode': 'codigo-barras-boleto', 'boleto_expiration_date': 'data-expiracao-boleto'})
        self.entregador.processa_dados_pagamento()
        self.entregador.dados_pagamento.should.be.equal({'conteudo_json': {'aplicacao': 'test', 'boleto_url': 'url-boleto', 'codigo_barras': 'codigo-barras-boleto', 'metodo': 'boleto', 'vencimento': 'data-expiracao-boleto'}, 'transacao_id': 'identificacao-id', 'valor_pago': '123.56'})

    @mock.patch('pagador_pagarme_boleto.servicos.EntregaPagamento.obter_conexao', mock.MagicMock())
    def test_processar_dados_de_pagamento_dispara_erro_se_invalido(self):
        self.entregador.dados_enviados = {'card_hash': None, 'capture': 'false', 'amount': 2900, 'installments': 1, 'payment_method': 'credit_card'}
        self.entregador.resposta = mock.MagicMock(status_code=400, sucesso=False, nao_autorizado=False, requisicao_invalida=True, conteudo={u'url': u'/transactions', u'errors': [{u'message': u'Nome do portador do cartão está faltando', u'type': u'invalid_parameter', u'parameter_name': u'card_holder_name'}, {u'message': u'Data de expiração do cartão está faltando', u'type': u'invalid_parameter', u'parameter_name': u'card_expiration_date'}], u'method': u'post'})
        self.entregador.processa_dados_pagamento.when.called_with().should.throw(
            self.entregador.EnvioNaoRealizado,
            u'\nDados inv\xe1lidos:\nNome do portador do cartão está faltando\nData de expiração do cartão está faltando'
        )

    @mock.patch('pagador_pagarme_boleto.servicos.EntregaPagamento.obter_conexao', mock.MagicMock())
    def test_processar_dados_de_pagamento_dispara_erro_sem_ser_parameter(self):
        self.entregador.dados_enviados = {'card_hash': None, 'capture': 'false', 'amount': 2900, 'installments': 1, 'payment_method': 'credit_card'}
        self.entregador.pedido = mock.MagicMock(numero=1234)
        self.entregador.resposta = mock.MagicMock(status_code=400, sucesso=False, requisicao_invalida=True, nao_autorizado=False, conteudo={u'url': u'/transactions', u'errors': [{u'message': u'Nome do portador do cartão está faltando', u'type': u'whatever'}, {u'message': u'Data de expiração do cartão está faltando', u'type': u'whatever'}], u'method': u'post'})
        self.entregador.processa_dados_pagamento.when.called_with().should.throw(
            self.entregador.EnvioNaoRealizado,
            u'Houve um erro de comunicação e sua compra não foi concluída. Por favor refaça o pedido.'
        )

    @mock.patch('pagador_pagarme_boleto.servicos.EntregaPagamento.obter_conexao', mock.MagicMock())
    def test_processar_dados_de_pagamento_dispara_erro_de_autorizacao(self):
        self.entregador.dados_enviados = {'card_hash': None, 'capture': 'false', 'amount': 2900, 'installments': 1, 'payment_method': 'credit_card'}
        self.entregador.resposta = mock.MagicMock(status_code=403, sucesso=False, requisicao_invalida=False, nao_autorizado=True, conteudo={u'url': u'/transactions', u'errors': [{u'message': u'api_key inválida', u'type': u'whatever'}], u'method': u'post'})
        self.entregador.processa_dados_pagamento.when.called_with().should.throw(
            self.entregador.EnvioNaoRealizado,
            u'Houve um erro de comunicação e sua compra não foi concluída. Por favor refaça o pedido.'
        )

    @mock.patch('pagador_pagarme_boleto.servicos.EntregaPagamento.obter_conexao', mock.MagicMock())
    def test_processar_dados_de_pagamento_define_identificador_id(self):
        self.entregador.configuracao = mock.MagicMock(aplicacao='test')
        self.entregador.pedido = mock.MagicMock(valor_total=15.70)
        self.entregador.resposta = mock.MagicMock(sucesso=True, requisicao_invalida=False, conteudo={'status': 'waiting_payment', 'id': 'identificacao-id', 'boleto_url': 'url-boleto', 'boleto_barcode': 'codigo-barras-boleto', 'boleto_expiration_date': 'data-expiracao-boleto'})
        self.entregador.processa_dados_pagamento()
        self.entregador.identificacao_pagamento.should.be.equal('identificacao-id')

    def test_envia_post_define_dados_da_entrega(self):
        self.entregador.conexao = mock.MagicMock()
        self.entregador.malote = mock.MagicMock()
        self.entregador.malote.to_dict.return_value = 'malote'
        self.entregador.envia_pagamento()
        self.entregador.dados_enviados.should.be.equal('malote')

    def test_envia_post_define_resposta_da_entrega(self):
        self.entregador.conexao = mock.MagicMock()
        self.entregador.conexao.post.return_value = 'resposta'
        self.entregador.malote = mock.MagicMock()
        self.entregador.malote.to_dict.return_value = 'malote'
        self.entregador.envia_pagamento()
        self.entregador.resposta.should.be.equal('resposta')

    def test_envia_post_chama_post_de_conexao(self):
        self.entregador.conexao = mock.MagicMock()
        self.entregador.url = 'url-envio'
        self.entregador.malote = mock.MagicMock()
        self.entregador.malote.to_dict.return_value = 'malote'
        self.entregador.envia_pagamento()
        self.entregador.conexao.post.assert_called_with('url-envio', 'malote')


class PagarMeBoletoRegistrandoNotificacao(unittest.TestCase):
    def test_nao_deve_definir_redirect(self):
        registrador = servicos.RegistraNotificacao(1234, {})
        registrador.redirect_para.should.be.none

    def test_nao_deve_montar_dados_pagamento(self):
        registrador = servicos.RegistraNotificacao(1234, {'id': 1234, 'current_status': 'paid'})
        registrador.monta_dados_pagamento()
        registrador.dados_pagamento.should.be.empty

    def test_deve_definir_situacao_pedido_pago(self):
        registrador = servicos.RegistraNotificacao(1234, {'id': 1234, 'current_status': 'paid'})
        registrador.monta_dados_pagamento()
        registrador.situacao_pedido.should.be.equal(servicos.servicos.SituacaoPedido.SITUACAO_PEDIDO_PAGO)

    def test_deve_definir_situacao_pedido_devolvido(self):
        registrador = servicos.RegistraNotificacao(1234, {'id': 1234, 'current_status': 'refunded'})
        registrador.monta_dados_pagamento()
        registrador.situacao_pedido.should.be.equal(servicos.servicos.SituacaoPedido.SITUACAO_PAGTO_DEVOLVIDO)

    def test_deve_definir_situacao_pedido_como_none_se_desconhecido(self):
        registrador = servicos.RegistraNotificacao(1234, {'id': 1234, 'current_status': 'zas'})
        registrador.monta_dados_pagamento()
        registrador.situacao_pedido.should.be.none

    def test_deve_definir_situacao_pedido_como_none_se_desconhecido(self):
        registrador = servicos.RegistraNotificacao(1234, {'id': 1234, 'current_status': 'zas'})
        registrador.monta_dados_pagamento()
        registrador.situacao_pedido.should.be.none

    def test_deve_retornar_resultado_ok(self):
        registrador = servicos.RegistraNotificacao(1234, {'id': 1234, 'current_status': 'paid'})
        registrador.monta_dados_pagamento()
        registrador.resultado.should.be.equal({'resultado': 'OK'})

    def test_deve_retornar_falha_se_nao_vier_status(self):
        registrador = servicos.RegistraNotificacao(1234, {'id': 1234})
        registrador.monta_dados_pagamento()
        registrador.resultado.should.be.equal({'resultado': 'FALHA', 'status_code': 500})
