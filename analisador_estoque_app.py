import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
import altair as alt
import matplotlib.pyplot as plt
import base64
import time


#fun￿ção para gerar gr￿áfico de barras
def criar_barras(coluna_num,coluna_cat,df):
    bars=alt.Chart(df,width=650,height=200).mark_bar().encode(
        x=alt.X(coluna_num, stack='zero'),
        y=alt.Y(coluna_cat),
        tooltip=[coluna_cat,coluna_num]).interactive()
    return bars

#streamlit
def main():
    st.title('Analisador de Mobilidade de Estoque\nIdentificador de SKUs sem giro + Recomendador de clientes')
    st.image('home.jpg', width=700)
    st.markdown('O objetivo principal desta ferramenta é realizar uma espécie de mapeamento da condição do estoque de uma empresa, '
                'classificando cada SKU em função do período sem vendas, da quantidade em estoque, da linha/família, do custo, '
                'entre outras análises. '
                'Após o entendimento da real condição do estoque, a ferramenta oferece a possibilidade de gerar uma lista de SKUs sem vendas '
                'há um determinado período, cruzando com os clientes potenciais que em algum momento já compraram tais SKUs. Dependendo do tipo de negócio '
                'da empresa, estes clientes podem ser potenciais para a realização de uma nova compra. De forma mais personalizada à cada business, '
                'esta ferramenta pode ser aprimorada através da aplicação de sistemas de recomendação baseados em técnicas de Machine Learning.')

    st.subheader('1. Mapeamento do Estoque')
    load_csv = st.radio('Deseja carregar um arquivo para análise?',('Sim, desejo carregar um arquivo CSV','Não, utilizar um arquivo demo da ferramenta'))
    
    if load_csv == 'Não, utilizar um arquivo demo da ferramenta':
        file = 'estoque_celular.csv'
        st.markdown('Estoque fictício de uma Assistencia Técnica de Celulares' )
    else:
        data=pd.DataFrame({'Linha_Familia':[''],'Codigo':[''],'Descrição':[''],'Data_Ultima_Venda':[''],'Qtd_Estoque':[''],'Custo_Total':['']} )
        st.markdown('O arquivo CSV a ser carregado deve conter as seguintes colunas: ')
        st.dataframe(data)
        file = st.file_uploader('Selecione o arquivo CSV contendo as colunas acima descritas',type='csv',
                            encoding='latin1')
    if file is not None:
        estoque = pd.read_csv(file, sep=";", decimal=",", encoding="Latin1", header=0,
                              names=['linha', 'codigo', 'descricao', 'ultima_venda', 'estoque_atual', 'custo_estoque'])
        estoque.linha = estoque['linha'].astype('str')
        estoque.estoque_atual = estoque['estoque_atual'].astype('int')
        estoque.ultima_venda = pd.to_datetime(estoque['ultima_venda'])
        estoque.sort_values(by='linha',inplace=True)

    ###########################################################################

    #Gráfico: Custo do Estoque x Linha
        st.subheader('Valor do Estoque x Linha')
        tot_linha = np.array(estoque.groupby('linha')['custo_estoque'].sum().round(0).reset_index())
        linha = tot_linha[:,0].astype('str')
        y0 = tot_linha[:, 1]
        x0 = tot_linha[:, 0]

        chart_data = pd.DataFrame()
        chart_data['linha'] = x0
        chart_data.linha = chart_data.linha.astype('str')
        chart_data['R$'] = y0
        st.write(criar_barras( 'linha','R$',chart_data))

    ###########################################################################

    #Checkbox: Mostrar valor total do estoque
        valor_tot = st.checkbox('Mostrar valor total do estoque')
        if valor_tot:
            st.write('R$ ', estoque.custo_estoque.sum())

    ###########################################################################

    #Checkbox: Mostrar composição do estoque em forma de tabela
        tab_estoque = st.checkbox('Mostrar em forma de tabela:')
        if tab_estoque:
            st.dataframe(chart_data)

    ###########################################################################

    #Slider: Escolher número de linhas que deseja visualizar
        number = st.slider('Escolha o número de linhas do dataset que deseja visualizar:', min_value=1,
                           max_value=len(estoque))
        st.dataframe(estoque.head(number))

    ###########################################################################

    #Botão: Mostrar o tipo das variáveis (colunas)
        if st.checkbox('Mostrar o tipo das variaveis (colunas)'):
            st.write(estoque.dtypes)

    ############################################################################

        estoque_atual_cat = []

        for j in (estoque['estoque_atual']):
            if j == 1:
                estoque_cat = '01'
            elif j == 2:
                estoque_cat = '02'
            elif j == 3:
                estoque_cat = '03'
            elif j == 4:
                estoque_cat = '04'
            elif j == 5:
                estoque_cat = '05'
            elif j > 5 and j <= 10:
                estoque_cat = '06-10'
            elif j > 10 and j <= 50:
                estoque_cat = '11-50'
            elif j > 50 and j <= 100:
                estoque_cat = '51-100'
            else:
                estoque_cat = 'Mais que 100'
            estoque_atual_cat.append(estoque_cat)
        estoque['estoque_atual_cat'] = estoque_atual_cat

        import datetime as dt
        today = pd.to_datetime(dt.datetime.today())
        estoque['giro'] = today - estoque['ultima_venda']
        # convertendo para dias inteiros
        estoque['giro'] = (estoque['giro'] / (3600000000000 * 24)).astype('int64')

        giro_cat = []
        # giro_mes=0
        for i, j in enumerate(estoque['giro']):
            if j <= 30:
                giro_mes = '000-030'
            elif j <= 60:
                giro_mes = '031-060'
            elif j <= 90:
                giro_mes = '061-090'
            elif j <= 120:
                giro_mes = '091-120'
            elif j <= 150:
                giro_mes = '121-150'
            elif j <= 180:
                giro_mes = '151-180'
            elif j <= 360:
                giro_mes = '181-360'
            else:
                giro_mes = 'Mais que 360d'
            giro_cat.append(giro_mes)
        estoque['giro_cat'] = giro_cat

    ###################################################################################################################

    # Selecionador de Grafico - Todas as Linhas
        st.subheader('2. Análise de quantidade e giro por SKU')

        escolher_linha_ou_todas = st.radio('', ('Pesquisar', 'Todas as linhas',
                                                'Escolher uma linha'))
        if escolher_linha_ou_todas == 'Todas as linhas':

            tipo_grafico = st.radio('Visualização de gráfico em função da(o):', ('Composição x Qtd de cada SKU',
                                         'Composição x Dias desde a última venda de cada SKU',
                                         'Custo x Qtd de cada SKU',
                                         'Custo x Dias desde a última venda de cada SKU'))

    ###################################################################################################################

        # Grafico 1
            if tipo_grafico == 'Composição x Qtd de cada SKU':
                qtd_sku = np.array(estoque.groupby('estoque_atual_cat')['codigo'].count().reset_index())
                qtd_sku_perc = qtd_sku.copy()
                qtd_sku_perc[:, 1] = ((qtd_sku[:, 1] / len(estoque)).astype('float64').round(2))
                y1 = qtd_sku[:, 1]
                x1 = qtd_sku[:, 0]
                y1p = qtd_sku_perc[:, 1]
                x1p = qtd_sku_perc[:, 0]
                plt.bar(x1, y1)
                for i in range(len(y1)):
                    plt.text(x=x1[i], y=y1[i] * 1.02, s=y1[i], size=12, ha='center', va='bottom')
                    plt.text(x=x1p[i], y=y1p[i] + (0.5 * y1[i]), s=y1p[i], size=12, ha='center', va='center', color='lightblue')
                plt.title('Todas as Linhas\nComposição x Qtd de cada SKU')
                plt.xlabel('Unidades por SKU')
                plt.ylabel('Qtd de SKUs')
                plt.xticks(rotation=15)
                plt.ylim((0, 1.2*y1.max()))
                st.pyplot()
                st.markdown('Distribuição do estoque em função da QUANTIDADE DE UNIDADES DE CADA SKU, '
                            'Ex: Qtd de SKUs que contém 01 unidade, qtd de SKUs que contém 02 unidades e assim por diante')
    ###################################################################################################################

        # Grafico2
            if tipo_grafico == 'Composição x Dias desde a última venda de cada SKU':
                giro_sku = np.array(estoque.groupby('giro_cat')['codigo'].count().reset_index())
                giro_sku_perc = giro_sku.copy()
                giro_sku_perc[:, 1] = (giro_sku[:, 1] / len(estoque)).astype('float64').round(2)
                y2 = giro_sku[:, 1]
                x2 = giro_sku[:, 0]
                y2p = giro_sku_perc[:, 1]
                x2p = giro_sku_perc[:, 0]
                plt.bar(x2, y2)
                for i in range(len(y2)):
                    plt.text(x=x2[i], y=y2[i] * 1.02, s=y2[i], size=12, ha='center', va='bottom')
                    plt.text(x=x2p[i], y=y2p[i] + (0.5 * y2[i]), s=y2p[i], size=12, ha='center', va='center', color='lightblue')
                plt.title('Todas as Linhas\nComposição x Dias desde a última venda de cada SKU')
                plt.xlabel('Dias desde a última venda')
                plt.xticks(rotation=15)
                plt.ylabel('Qtd de SKUs')
                plt.ylim((0, 1.2*y2.max()))
                st.pyplot()
                st.markdown('Distribuição do estoque em função dos DIAS DESDE A ÚLTIMA VENDA DE CADA SKU. '
                            'Ex: Qtd de SKUs que apresentaram venda nos últimos 030 dias, entre 031-060 dias e assim por diante' )
    ###################################################################################################################

        # Grafico3
            if tipo_grafico == 'Custo x Qtd de cada SKU':
                qtd_sku = np.array(estoque.groupby('estoque_atual_cat')['custo_estoque'].sum().round(0).reset_index())
                qtd_sku_perc = qtd_sku.copy()
                qtd_sku_perc[:, 1] = (qtd_sku[:, 1] / (estoque.custo_estoque.sum())).astype('float64').round(2)
                y3 = qtd_sku[:, 1]
                x3 = qtd_sku[:, 0]
                y3p = qtd_sku_perc[:, 1]
                x3p = qtd_sku_perc[:, 0]
                plt.bar(x3, y3)
                for i in range(len(y3)):
                    plt.text(x=x3[i], y=y3[i] * 1.05, s=y3[i], size=12, ha='center', va='bottom',rotation=90)
                    plt.text(x=x3p[i], y=y3p[i] + (0.5 * y3[i]), s=y3p[i], size=12, ha='center', va='center', color='lightblue')
                plt.title('Todas as Linhas\nCusto x Qtd de cada SKU')
                plt.xlabel('Unidades x SKU')
                plt.xticks(rotation=15)
                plt.ylabel('R$')
                plt.ylim((0, 1.4*y3.max()))
                st.pyplot()
                st.markdown('Custo do estoque em função da QUANTIDADE DE UNIDADES DE CADA SKU, '
                            'Ex: Custo dos SKUs que contém 01 unidade, Custo dos SKUs que contém 02 unidades e assim por diante')

    ###################################################################################################################

        # Grafico4
            if tipo_grafico == 'Custo x Dias desde a última venda de cada SKU':
                giro_soma = np.array(estoque.groupby('giro_cat')['custo_estoque'].sum().round(0).reset_index())
                giro_soma_perc = giro_soma.copy()
                giro_soma_perc[:, 1] = (giro_soma[:, 1] / (estoque.custo_estoque.sum())).astype('float64').round(2)
                y4 = giro_soma[:, 1]
                x4 = giro_soma[:, 0]
                y4p = giro_soma_perc[:, 1]
                x4p = giro_soma_perc[:, 0]
                plt.bar(x4, y4)
                for i in range(len(y4)):
                    plt.text(x=x4[i], y=y4[i] * 1.05, s=y4[i], size=12, ha='center', va='bottom', rotation=90)
                    plt.text(x=x4p[i], y=y4p[i] + (0.5 * y4[i]), s=y4p[i], size=12, ha='center', va='center', color='lightblue')
                plt.title(
                    'Todas as Linhas\nCusto x Dias desde a última venda de cada SKU')
                plt.xlabel('Dias desde a última venda')
                plt.xticks(rotation=15)
                plt.ylabel('R$')
                plt.ylim((0, 1.4*y4.max()))
                st.pyplot()
                st.markdown('Custo do estoque em função dos DIAS DESDE A ÚLTIMA VENDA DE CADA SKU. '
                        'Ex: Custo dos SKUs que apresentaram venda nos últimos 030 dias, entre 031-060 dias e assim por diante')


    ###################################################################################################################
    # Selecionador de Grafico - Escolha da Linha - Escolha do período sem vendas
        if escolher_linha_ou_todas == 'Escolher uma linha':
            linha_escolhida = st.selectbox('Defina uma linha: ', x0)
            estoque_pesquisa = estoque.copy()
            estoque_pesquisa = estoque_pesquisa[estoque_pesquisa['linha'] == linha_escolhida]

            tipo_grafico_linha = st.radio('Visualização de gráfico em função de:', ('Composição x Qtd de cada SKU',
                                         'Composição x Dias desde a última venda de cada SKU',
                                         'Custo x Qtd de cada SKU',
                                         'Custo x Dias desde a última venda de cada SKU'))

    ###################################################################################################################

        # Grafico5
            if tipo_grafico_linha == 'Composição x Qtd de cada SKU':

                qtd_sku = np.array(estoque_pesquisa.groupby('estoque_atual_cat')['codigo'].count().reset_index())
                qtd_sku_perc = qtd_sku.copy()
                qtd_sku_perc[:, 1] = ((qtd_sku[:, 1] / len(estoque_pesquisa)).astype('float64').round(2))
                y1 = qtd_sku[:, 1]
                x1 = qtd_sku[:, 0]
                y1p = qtd_sku_perc[:, 1]
                x1p = qtd_sku_perc[:, 0]
                plt.bar(x1, y1,color='darkorange')
                for i in range(len(y1)):
                    plt.text(x=x1[i], y=y1[i]*1.02, s=y1[i], size=12, ha='center', va='bottom')
                    plt.text(x=x1p[i], y=y1p[i]+(0.5*y1[i]), s=y1p[i], size=12, ha='center', va='center', color='w')
                plt.title(f'Linha {linha_escolhida}\nComposição x Qtd de cada SKU')
                plt.xlabel('Unidades por SKU')
                plt.ylabel('Qtd de SKUs')
                plt.xticks(rotation=15)
                plt.ylim((0, 1.2*y1.max()))
                st.pyplot()
                st.markdown('Distribuição do estoque em função da QUANTIDADE DE UNIDADES DE CADA SKU, '
                            'Ex: Qtd de SKUs que contém 01 unidade, qtd de SKUs que contém 02 unidades e assim por diante')
        ###################################################################################################################

        # Grafico6
            if tipo_grafico_linha == 'Composição x Dias desde a última venda de cada SKU':
                giro_sku = np.array(estoque_pesquisa.groupby('giro_cat')['codigo'].count().reset_index())
                giro_sku_perc = giro_sku.copy()
                giro_sku_perc[:, 1] = (giro_sku[:, 1] / len(estoque_pesquisa)).astype('float64').round(2)
                y2 = giro_sku[:, 1]
                x2 = giro_sku[:, 0]
                y2p = giro_sku_perc[:, 1]
                x2p = giro_sku_perc[:, 0]
                plt.bar(x2, y2,color='darkorange')
                for i in range(len(y2)):
                    plt.text(x=x2[i], y=y2[i] * 1.02, s=y2[i], size=12, ha='center', va='bottom')
                    plt.text(x=x2p[i], y=y2p[i] + (0.5 * y2[i]), s=y2p[i], size=12, ha='center', va='center', color='w')
                plt.title(f'Linha {linha_escolhida}\nComposição x Dias desde a última venda de cada SKU')
                plt.xlabel('Dias desde a última venda')
                plt.xticks(rotation=15)
                plt.ylabel('Qtd de SKUs')
                plt.ylim((0, 1.2*y2.max()))
                st.pyplot()
                st.markdown('Distribuição do estoque em função dos DIAS DESDE A ÚLTIMA VENDA DE CADA SKU. '
                            'Ex: Qtd de SKUs que apresentaram venda nos últimos 030 dias, entre 031-060 dias e assim por diante' )
        ###################################################################################################################

        #Grafico7
            if tipo_grafico_linha == 'Custo x Qtd de cada SKU':
                qtd_sku = np.array(estoque_pesquisa.groupby('estoque_atual_cat')['custo_estoque'].sum().round(0).reset_index())
                qtd_sku_perc = qtd_sku.copy()
                qtd_sku_perc[:, 1] = (qtd_sku[:, 1] / (estoque_pesquisa.custo_estoque.sum())).astype('float64').round(2)
                y3 = qtd_sku[:, 1]
                x3 = qtd_sku[:, 0]
                y3p = qtd_sku_perc[:, 1]
                x3p = qtd_sku_perc[:, 0]
                plt.bar(x3, y3,color='darkorange')
                for i in range(len(y3)):
                    plt.text(x=x3[i], y=y3[i] * 1.05, s=y3[i], size=12, ha='center', va='bottom', rotation=90)
                    plt.text(x=x3p[i], y=y3p[i] + (0.5 * y3[i]), s=y3p[i], size=12, ha='center', va='center', color='w')
                plt.title(f'Linha {linha_escolhida}\nCusto x Qtd de cada SKU')
                plt.xlabel('Unidades x SKU')
                plt.xticks(rotation=15)
                plt.ylabel('R$')
                plt.ylim((0, 1.4*y3.max()))
                st.pyplot()
                st.markdown('Custo do estoque em função da QUANTIDADE DE UNIDADES DE CADA SKU, '
                            'Ex: Custo dos SKUs que contém 01 unidade, Custo dos SKUs que contém 02 unidades e assim por diante')

        ###################################################################################################################

        #Grafico8
            if tipo_grafico_linha == 'Custo x Dias desde a última venda de cada SKU':
                giro_soma = np.array(estoque_pesquisa.groupby('giro_cat')['custo_estoque'].sum().round(0).reset_index())
                giro_soma_perc = giro_soma.copy()
                giro_soma_perc[:, 1] = (giro_soma[:, 1] / (estoque_pesquisa.custo_estoque.sum())).astype('float64').round(2)
                y4 = giro_soma[:, 1]
                x4 = giro_soma[:, 0]
                y4p = giro_soma_perc[:, 1]
                x4p = giro_soma_perc[:, 0]
                plt.bar(x4, y4,color='darkorange')
                for i in range(len(y4)):
                    plt.text(x=x4[i], y=y4[i] * 1.05, s=y4[i], size=12, ha='center', va='bottom', rotation=90)
                    plt.text(x=x4p[i], y=y4p[i] + (0.5 * y4[i]), s=y4p[i], size=12, ha='center', va='center', color='w')
                plt.title(f'Linha {linha_escolhida}\nCusto x Dias desde a última venda de cada SKU')
                plt.xlabel('Dias desde a última venda')
                plt.xticks(rotation=15)
                plt.ylabel('R$')
                plt.ylim((0, 1.4*y4.max()))
                st.pyplot()
                st.markdown('Custo do estoque em função dos DIAS DESDE A ÚLTIMA VENDA DE CADA SKU. '
                        'Ex: Custo dos SKUs que apresentaram venda nos últimos 030 dias, entre 031-060 dias e assim por diante')

    ###################################################################################################################
    ###################################################################################################################

        # Gerando lista de itens sem vendas há "X" dias cruzando com
    # clientes potenciais que em algum momento já compraram estes itens

        st.subheader('3. Gerando uma lista de SKUs sem vendas há "X" dias ')
        st.markdown('Com recomendação de clientes potenciais que em algum momento já compraram estes itens sem giro')

        if load_csv == 'Não, utilizar um arquivo demo da ferramenta':
            file2='vendas_celular.csv'
        else:
            # carregando a planilha vendas_cliente
            st.markdown('O arquivo CSV a ser carregado deve conter as seguintes colunas:')
            data2 = pd.DataFrame({'Codigo': [''], 'Data_Venda': [''], 'Cliente': ['']})
            st.dataframe(data2)
            file2 = st.file_uploader('Selecione o arquivo CSV de Vendas contendo as colunas acima descritas', type='csv',
                                 encoding='latin1')
        if file2 is not None:
            clientes = pd.read_csv(file2, sep=';', decimal=',', encoding="Latin1", header=0,
                                   names=['codigo', 'data_venda', 'cliente'])
            clientes = clientes.fillna("-")

            uma_linha_ou_todas = st.radio(' ', ('Pesquisar','Todas as linhas',
                                         'Escolher uma linha'))

            if uma_linha_ou_todas == 'Escolher uma linha':
                linha_escolhida2 = st.selectbox('Defina uma linha:', x0)
                giro_escolhido = st.slider('SKUs sem vendas há mais de quantos dias?',min_value=1, max_value=360)
                if giro_escolhido == 1:
                    st.warning('Deslize a barra acima para um valor maior que 1')
                else:
                    with st.spinner('Processando arquivo csv para download...'):
                        time.sleep(5)
                        pesquisa = estoque.copy()
                        pesquisa = pesquisa[(pesquisa['giro'] >= giro_escolhido) & (pesquisa['linha'] == linha_escolhida2)].reset_index()



                        #vlookup dos clientes para cada SKU a ser ofertada
                        lista_cliente=[]
                        for i in pesquisa.codigo:
                            cliente_parcial = []
                            for j,k in enumerate(clientes.codigo):
                                if k == i:
                                    c = clientes.iloc[j,2]
                                    if c not in cliente_parcial:
                                        cliente_parcial.append(c)
                                else:
                                    pass
                            lista_cliente.append(cliente_parcial)
                        pesquisa['cliente'] = pd.Series(lista_cliente)
                        pesquisa.drop('index', axis=1, inplace=True)
                        pesquisa.rename(columns={'giro':'sem_giro_ha','giro_cat':'sem_giro_ha_cat'},inplace=True)

                        st.write(f'Qtd. de SKUs: {pesquisa.shape[0]}')
                        st.write(f'Custo total: R$ {pesquisa.custo_estoque.sum().round(2)}')
                        st.write(f'SKUs sem vendas há mais de {giro_escolhido} dias - Linha {linha_escolhida2}')
                        st.dataframe(pesquisa)
                    st.success('Pronto!')

                    # exportando planilha em CSV para Vendas oferecer aos clientes que já compraram cada item
                    if st.checkbox('Baixar arquivo csv'):
                        #pesquisa.to_excel(f'Itens_sem_venda_ha_mais_de_{giro_escolhido}_dias - Linha {linha_escolhida2}.xlsx',
                        #                  index=False)
                        df = pesquisa
                        csv = df.to_csv(sep=';',decimal=',',index=False)
                        b64 = base64.b64encode(csv.encode()).decode()  # some strings <-> bytes conversions necessary here
                        href = f'<a href="data:file/csv;base64,{b64}">Download CSV File</a> (right-click and save as ' \
                            f'&lt;some_name&gt;.csv)'
                        st.markdown(href, unsafe_allow_html=True)

            elif uma_linha_ou_todas == 'Todas as linhas':
                giro_escolhido = st.slider('SKUs sem vendas há mais de quantos dias?', min_value=1, max_value=360)
                if giro_escolhido == 1:
                    st.warning('Deslize a barra acima para um valor maior que 1')
                else:
                    with st.spinner('Processando arquivo csv para download...'):
                        time.sleep(5)

                        pesquisa = estoque.copy()
                        pesquisa = pesquisa[pesquisa['giro'] >= giro_escolhido].reset_index()

                        # vlookup dos clientes para cada SKU a ser ofertada
                        lista_cliente = []
                        for i in pesquisa.codigo:
                            cliente_parcial = []
                            for j, k in enumerate(clientes.codigo):
                                if k == i:
                                    c = clientes.iloc[j, 2]
                                    if c not in cliente_parcial:
                                        cliente_parcial.append(c)
                                else:
                                    pass
                            lista_cliente.append(cliente_parcial)
                        pesquisa['cliente'] = pd.Series(lista_cliente)
                        pesquisa.drop('index',axis=1,inplace=True)
                        pesquisa.rename(columns={'giro':'sem_giro_ha','giro_cat':'sem_giro_cat_ha'},inplace=True)

                        st.write(f'Qtd. de SKUs: {pesquisa.shape[0]}')
                        st.write(f'Custo total: R$ {pesquisa.custo_estoque.sum().round(2)}')
                        st.write(f'SKUs sem vendas há mais de {giro_escolhido} dias - Todas as linhas')
                        st.dataframe(pesquisa)
                    st.success('Pronto!')

            # Exportando planilha em CSV para Vendas oferecer aos clientes que já compraram cada item

                    if st.checkbox('Baixar arquivo csv'):
                        #pesquisa.to_excel(f'Itens_sem_venda_ha_mais_de_{giro_escolhido}_dias - Todas as linhas.xlsx',
                        #                  index=False)
                        df = pesquisa
                        csv = df.to_csv(sep=';',decimal=',',index=False)
                        b64 = base64.b64encode(csv.encode()).decode()  # some strings <-> bytes conversions necessary here
                        href = f'<a href="data:file/csv;base64,{b64}">Download CSV File</a> (right-click and save as ' \
                            f'&lt;some_name&gt;.csv)'
                        st.markdown(href, unsafe_allow_html=True)
        #######################################################################################################                          index=False)

            else:
                    st.warning('Escolha entre "Todas as linhas" ou "Escolher uma linha" ')



###################################################################################################################

if __name__ == '__main__':
	main()