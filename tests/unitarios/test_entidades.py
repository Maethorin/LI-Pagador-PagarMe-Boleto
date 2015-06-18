# -*- coding: utf-8 -*-
import unittest
from decimal import Decimal
from datetime import datetime

import mock

from pagador_pagarme_boleto import entidades


class PagarMeBoletoConfiguracaoMeioPagamento(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(PagarMeBoletoConfiguracaoMeioPagamento, self).__init__(*args, **kwargs)
        self.campos = ['ativo', 'aplicacao', 'token', 'valor_minimo_aceitado', 'json']
        self.codigo_gateway = 15

    @mock.patch('pagador_pagarme_boleto.entidades.ConfiguracaoMeioPagamento.preencher_gateway', mock.MagicMock())
    def test_deve_ter_os_campos_especificos_na_classe(self):
        entidades.ConfiguracaoMeioPagamento(234).campos.should.be.equal(self.campos)

    @mock.patch('pagador_pagarme_boleto.entidades.ConfiguracaoMeioPagamento.preencher_gateway', mock.MagicMock())
    def test_deve_ter_codigo_gateway(self):
        entidades.ConfiguracaoMeioPagamento(234).codigo_gateway.should.be.equal(self.codigo_gateway)

    @mock.patch('pagador_pagarme_boleto.entidades.ConfiguracaoMeioPagamento.preencher_gateway', autospec=True)
    def test_deve_preencher_gateway_na_inicializacao(self, preencher_mock):
        configuracao = entidades.ConfiguracaoMeioPagamento(234)
        preencher_mock.assert_called_with(configuracao, self.codigo_gateway, self.campos)

    @mock.patch('pagador_pagarme_boleto.entidades.ConfiguracaoMeioPagamento.preencher_gateway', mock.MagicMock())
    def test_deve_definir_formulario_na_inicializacao(self):
        configuracao = entidades.ConfiguracaoMeioPagamento(234)
        configuracao.formulario.should.be.a('pagador_pagarme_boleto.cadastro.FormularioPagarMeBoleto')

    @mock.patch('pagador_pagarme_boleto.entidades.ConfiguracaoMeioPagamento.preencher_gateway', mock.MagicMock())
    def test_nao_deve_ser_aplicacao(self):
        configuracao = entidades.ConfiguracaoMeioPagamento(234)
        configuracao.eh_aplicacao.should.be.falsy

    @mock.patch('pagador_pagarme_boleto.entidades.ConfiguracaoMeioPagamento.preencher_gateway', mock.MagicMock())
    def test_deve_ser_gateway(self):
        configuracao = entidades.ConfiguracaoMeioPagamento(234)
        configuracao.eh_gateway.should.be.truthy


class PagarMeBoletoMontandoMalote(unittest.TestCase):
    def __init__(self, methodName='runTest'):
        super(PagarMeBoletoMontandoMalote, self).__init__(methodName)
        self.pedido = mock.MagicMock(
            numero=123,
            valor_total=Decimal('14.00'),
            cliente={
                'nome': 'Cliente Teste',
                'email': 'email@cliente.com',
            },
            cliente_documento='12345678901',
            cliente_telefone=('11', '23456789'),
            endereco_cliente={
                'endereco': 'Rua Teste',
                'numero': 123,
                'complemento': 'Apt 101',
                'bairro': 'Teste',
                'cep': '10234000'
            },
            itens=[
                entidades.entidades.ItemDePedido(nome='Produto 1', sku='PROD01', quantidade=1, preco_venda=Decimal('40.00')),
                entidades.entidades.ItemDePedido(nome='Produto 2', sku='PROD02', quantidade=1, preco_venda=Decimal('50.00')),
            ]
        )

    def test_malote_deve_ter_propriedades(self):
        entidades.Malote('configuracao').to_dict().should.be.equal({'amount': None, 'boleto_expiration_date': None, 'customer': None, 'metadata': None, 'payment_method': 'boleto', 'postback_url': None})

    @mock.patch('pagador_pagarme_boleto.entidades.datetime')
    def test_deve_montar_conteudo(self, datetime_mock):
        datetime_mock.now.return_value = datetime(2015, 6, 12, 15, 30)
        malote = entidades.Malote(mock.MagicMock(loja_id=8, json={'dias_vencimento': 4}))
        parametros = {}
        malote.monta_conteudo(self.pedido, parametros, {})
        malote.to_dict().should.be.equal({'amount': 1400, 'boleto_expiration_date': '2015-06-16T15:30:00', 'customer': {'address': {'complementary': 'Apt 101', 'neighborhood': 'Teste', 'street': 'Rua Teste', 'street_number': 123, 'zipcode': '10234000'}, 'document_number': '12345678901', 'email': 'email@cliente.com', 'name': 'Cliente Teste', 'phone': {'ddd': '11', 'number': '23456789'}}, 'metadata': {'carrinho': [{'nome': 'Produto 1', 'preco_venda': 40.0, 'quantidade': 1, 'sku': 'PROD01'}, {'nome': 'Produto 2', 'preco_venda': 50.0, 'quantidade': 1, 'sku': 'PROD02'}], 'pedido_numero': 123}, 'payment_method': 'boleto', 'postback_url': 'http://localhost:5000/pagador/meio-pagamento/pmboleto/retorno/8/notificacao?referencia=123'})
