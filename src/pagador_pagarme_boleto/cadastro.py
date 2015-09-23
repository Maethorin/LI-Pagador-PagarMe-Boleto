# -*- coding: utf-8 -*-

from li_common.padroes import cadastro
from li_common.comunicacao import requisicao


class BoletoValidador(cadastro.ValidadorBase):
    @property
    def eh_valido(self):
        if type(self.valor) is not dict:
            self.erros['dados_invalidos'] = u'Os dados do boleto devem ser em formato de dicionário'
            return False
        if int(self.valor.get('dias_vencimento', 0) or 0) <= 0:
            self.erros['dias_vencimento'] = u'Dias para o vencimento deve ser maior que 0 (zero).'
        return not self.erros


class DescontoValidador(cadastro.ValidadorBase):
    @property
    def eh_valido(self):
        try:
            valor = float(self.valor)
            if valor > 100.0 or valor < 0.0:
                self.erros = u'Porcentagem inválida. Insira um valor entre 0% e 100%.'
        except (TypeError, ValueError):
            self.erros = u'Porcentagem inválida. Insira um valor entre 0% e 100%.'
        return not self.erros


class AmbienteValidador(cadastro.ValidadorBase):
    @property
    def eh_valido(self):
        resposta = requisicao.Conexao(formato_envio=requisicao.Formato.querystring).get('https://api.pagar.me/1/company', dados={'api_key': self.valores['token']})
        if not resposta.sucesso:
            return True
        if self.valor == 'L':
            valido = resposta.conteudo['status'] == 'active'
            if not valido:
                self.erros = u'Sua loja não está live no Pagar.Me. Altere primeiro no Dashboard do Pagar.Me antes de atualizar na Loja Integrada.'
            return valido
        return True


class ChaveApiValidador(cadastro.ValidadorBase):
    @property
    def eh_valido(self):
        resposta = requisicao.Conexao(formato_envio=requisicao.Formato.querystring).get('https://api.pagar.me/1/company', dados={'api_key': self.valor})
        if not resposta.sucesso:
            self.erros = u'A Chave de Api digitada não é válida. Se você está tentando usar a chave de api LIVE, altere sua loja para LIVE primeiro no Pagar.Me.'
            return False
        if self.valor.startswith('ak_live'):
            valido = resposta.conteudo['status'] == 'active'
            if not valido:
                self.erros = u'Sua loja não está live no Pagar.Me. Altere primeiro no Dashboard do Pagar.Me antes de usar a chave de api live.'
            return valido
        return True


class FormularioPagarMeBoleto(cadastro.Formulario):
    dados_boleto = cadastro.CampoFormulario('json', ordem=0, tipo=cadastro.TipoDeCampo.oculto, formato=cadastro.FormatoDeCampo.json, validador=BoletoValidador)

    ativo = cadastro.CampoFormulario('ativo', 'Pagamento ativo?', tipo=cadastro.TipoDeCampo.boleano, ordem=1)
    ambiente = cadastro.CampoFormulario('aplicacao', u'Ambiente', tipo=cadastro.TipoDeCampo.escolha, validador=AmbienteValidador, requerido=True, opcoes=(('T', u'test'), ('L', u'live')), ordem=2, texto_ajuda=u'Use test para validar sua integração com o PAGAR.ME. Ao alterar essa opção para live, você também deve alterar sua conta no PAGAR.ME para live.')
    chave_api = cadastro.CampoFormulario('token', u'Chave de API', requerido=True, tamanho_max=128, ordem=3, validador=ChaveApiValidador, texto_ajuda=u'Copie a chave do seu dashboard Pagar.me e cole aqui')
    tem_desconto = cadastro.CampoFormulario('desconto', u'Usar desconto?', requerido=False, ordem=4, tipo=cadastro.TipoDeCampo.boleano, texto_ajuda=u'Marque esse campo caso você queira aplicar o desconto no pagamento via boleto.')
    desconto_valor = cadastro.CampoFormulario('desconto_valor', u'Desconto aplicado', requerido=False, ordem=5, decimais=2, tipo=cadastro.TipoDeCampo.decimal, validador=DescontoValidador)
    aplicar_no_total = cadastro.CampoFormulario('aplicar_no_total', u'Aplicar no total?', requerido=False, ordem=6, tipo=cadastro.TipoDeCampo.boleano, texto_ajuda=u'Aplicar desconto no total da compra (incluir por exemplo o frete).')
    valor_minimo_aceitado = cadastro.CampoFormulario('valor_minimo_aceitado', u'Valor mínimo', requerido=False, decimais=2, ordem=7, tipo=cadastro.TipoDeCampo.decimal, texto_ajuda=u'Informe o valor mínimo para exibir esta forma de pagamento.')
