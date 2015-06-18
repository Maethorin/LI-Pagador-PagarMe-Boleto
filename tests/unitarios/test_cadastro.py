# -*- coding: utf-8 -*-
import unittest

from pagador_pagarme_boleto import cadastro


class FormularioPagarMeBoleto(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(FormularioPagarMeBoleto, self).__init__(*args, **kwargs)
        self.formulario = cadastro.FormularioPagarMeBoleto()

    def test_deve_ter_dados_boleto(self):
        self.formulario.dados_boleto.nome.should.be.equal('json')
        self.formulario.dados_boleto.ordem.should.be.equal(0)
        self.formulario.dados_boleto.tipo.should.be.equal(cadastro.cadastro.TipoDeCampo.oculto)

    def test_deve_ter_ativo(self):
        self.formulario.ativo.nome.should.be.equal('ativo')
        self.formulario.ativo.ordem.should.be.equal(1)
        self.formulario.ativo.label.should.be.equal('Pagamento ativo?')
        self.formulario.ativo.tipo.should.be.equal(cadastro.cadastro.TipoDeCampo.boleano)

    def test_deve_ter_ambiente(self):
        self.formulario.ambiente.nome.should.be.equal('aplicacao')
        self.formulario.ambiente.ordem.should.be.equal(2)
        self.formulario.ambiente.label.should.be.equal(u'Ambiente')
        self.formulario.ambiente.tipo.should.be.equal(cadastro.cadastro.TipoDeCampo.escolha)
        self.formulario.ambiente.opcoes.should.be.equal((('T', u'test'), ('L', u'live')))

    def test_deve_ter_chave_api(self):
        self.formulario.chave_api.nome.should.be.equal('token')
        self.formulario.chave_api.ordem.should.be.equal(3)
        self.formulario.chave_api.label.should.be.equal(u'Chave de API')
        self.formulario.chave_api.tamanho_max.should.be.equal(128)
        self.formulario.chave_api.requerido.should.be.truthy

    def test_deve_ter_valor_minimo_aceitado(self):
        self.formulario.valor_minimo_aceitado.nome.should.be.equal('valor_minimo_aceitado')
        self.formulario.valor_minimo_aceitado.ordem.should.be.equal(5)
        self.formulario.valor_minimo_aceitado.label.should.be.equal(u'Valor mínimo')
        self.formulario.valor_minimo_aceitado.tipo.should.be.equal(cadastro.cadastro.TipoDeCampo.decimal)
