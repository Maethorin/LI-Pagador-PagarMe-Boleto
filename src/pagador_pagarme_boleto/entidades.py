# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
from pagador import settings, entidades
from pagador_pagarme_boleto import cadastro

CODIGO_GATEWAY = 15
GATEWAY = 'pmboleto'


class Cliente(entidades.BaseParaPropriedade):
    _atributos = ['name', 'document_number', 'email', 'address', 'phone']


class Endereco(entidades.BaseParaPropriedade):
    _atributos = ['street', 'neighborhood', 'zipcode', 'street_number', 'complementary']


class Telefone(entidades.BaseParaPropriedade):
    _atributos = ['ddd', 'number']


class Malote(entidades.Malote):
    def __init__(self, configuracao):
        super(Malote, self).__init__(configuracao)
        self.payment_method = 'boleto'
        self.boleto_expiration_date = None
        self.amount = None
        self.postback_url = None
        self.customer = None
        self.metadata = None

    def monta_conteudo(self, pedido, parametros_contrato=None, dados=None):
        self.boleto_expiration_date = (datetime.now() + timedelta(days=self.configuracao.json['dias_vencimento'])).isoformat()
        self.amount = self.formatador.formata_decimal(pedido.valor_total, em_centavos=True)
        url_notificacao = settings.NOTIFICACAO_URL.format(GATEWAY, self.configuracao.loja_id)
        self.postback_url = '{}/notificacao?referencia={}'.format(url_notificacao, pedido.numero)
        self.customer = Cliente(
            name=pedido.cliente['nome'],
            document_number=pedido.cliente_documento,
            email=pedido.cliente['email'],
            address=Endereco(
                street=pedido.endereco_cliente['endereco'],
                street_number=pedido.endereco_cliente['numero'],
                complementary=pedido.endereco_cliente['complemento'],
                neighborhood=pedido.endereco_cliente['bairro'],
                zipcode=pedido.endereco_cliente['cep'],
            ),
            phone=Telefone(ddd=pedido.cliente_telefone[0], number=pedido.cliente_telefone[1])
        )
        self.metadata = {
            'pedido_numero': pedido.numero,
            'carrinho': [item.to_dict() for item in pedido.itens]
        }


class ConfiguracaoMeioPagamento(entidades.ConfiguracaoMeioPagamento):
    def __init__(self, loja_id, codigo_pagamento=None, eh_listagem=False):
        self.campos = ['ativo', 'aplicacao', 'token', 'valor_minimo_aceitado', 'json']
        self.codigo_gateway = CODIGO_GATEWAY
        self.eh_gateway = True
        super(ConfiguracaoMeioPagamento, self).__init__(loja_id, codigo_pagamento, eh_listagem=eh_listagem)
        if not self.eh_listagem:
            self.formulario = cadastro.FormularioPagarMeBoleto()
