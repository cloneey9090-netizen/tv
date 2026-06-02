import os
import re
import requests
import datetime
import time  # <--- Nova ferramenta para dar um tempo de espera (delay) de segurança

# =====================================================================
#                 PAINEL DE CONTROLE DO COMANDANTE
# =====================================================================
# LINK DIRETO DO SEU GOOGLE DRIVE (O ROBO VAI LER DAQUI)
LINK_DRIVE_COMANDANTE = "https://drive.google.com/uc?id=1kk-OsN3R02flYm2Nl0kYZ7qI3JdzhwB_&export=download"

# MIRA SINTONIZADA NO PIRATETV (FONTES DE BUSCA)
PIRATE_TV_URL = "https://piratetv.sk"

# CABEÇALHO DE CAMUFLAGEM: Faz o robô fingir que é um celular Android comum
HEADERS_CAMUFLAGEM = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36"
}

# CANAIS QUE O ROBÔ VAI CAÇAR PARA JOGAR NA PARTE DE BAIXO
CANAIS_ALVO = [
    "Premiere", "Globoplay Novelas", "Gloob", "Globo SP",
    "Sportv 1", "Sportv 2", "Sportv 3", "ESPN 1", "ESPN 2"
]
# =====================================================================

def baixar_lista_do_drive():
    print("📁 Conectando ao Google Drive do Comandante...")
    try:
        resposta = requests.get(LINK_DRIVE_COMANDANTE, timeout=15)
        if resposta.status_code == 200:
            print("👍 Lista do Drive baixada com sucesso!")
            return resposta.text.split("\n")
        else:
            print(f"❌ Erro ao acessar o Drive (Status: {resposta.status_code})")
            return []
    except Exception as e:
        print(f"❌ Falha na conexão com o Drive: {e}")
        return []

def caçar_links():
    links_finais = {}
    print("🤖 Caçador ativo com camuflagem de celular de olho no PirateTV...")
    
    try:
        # Acessa o site usando a camuflagem para passar direto pela portaria
        resposta = requests.get(PIRATE_TV_URL, headers=HEADERS_CAMUFLAGEM, timeout=15)
        
        if resposta.status_code == 200:
            texto_do_site = resposta.text
            
            for alvo in CANAIS_ALVO:
                # O robô procura pelo nome do canal e captura o link .m3u8 mais próximo dele
                # Essa expressão regular vasculha o código HTML atrás da fiação oculta
                padrao = rf'"{alvo}".*?(https?://[^\s"\']+\.m3u8)'
                resultado = re.search(padrao, texto_do_site, re.IGNORECASE | re.DOTALL)
                
                if resultado:
                    link_encontrado = resultado.group(1).strip()
                    links_finais[alvo] = link_encontrado
                    print(f"🎯 Canal encontrado com sucesso: {alvo}")
                else:
                    print(f"⚠️ Link do canal [{alvo}] não estava visível nesta ronda.")
                
                # LENTIDÃO PROGRAMADA: Espera 2 segundos antes de checar o próximo para não ativar o alarme do site
                time.sleep(2)
                
        else:
            print(f"❌ PirateTV recusou o acesso do robô (Status: {resposta.status_code})")
            
    except Exception as e:
        print(f"❌ Erro crítico na mineração do PirateTV: {e}")
        
    return links_finais

def gerenciar_fortaleza():
    conteudo_base = baixar_lista_do_drive()

    if not conteudo_base and os.path.exists("lista.txt"):
        print("⚠️ Usando lista local como segurança pois o Drive não respondeu.")
        with open("lista.txt", "r", encoding="utf-8") as f:
            conteudo_base = f.readlines()

    if not conteudo_base:
        conteudo_base = ["#EXTM3U\n"]
    
    data_atual = datetime.datetime.now().strftime("%d/%m/%Y às %H:%M")
    linha_data = f"# LISTA MANTIDA VIVA EM: {data_atual}\n"
    
    lista_canais_atualizada = []
    primeira_linha = conteudo_base[0].strip() + "\n"
    lista_canais_atualizada.append(primeira_linha)
    
    inicio = 1
    if len(conteudo_base) > 1 and conteudo_base[1].startswith("# LISTA MANTIDA VIVA"):
        inicio = 2
        
    lista_canais_atualizada.append(linha_data)
    
    novos_links = caçar_links()
    i = inicio
    canais_processados = set()
    
    while i < len(conteudo_base):
        linha = conteudo_base[i].strip()
        if not linha:
            i += 1
            continue
            
        match = re.search(r'#EXTINF:.*,\s*(.*)', linha)
        if match:
            nome_canal_lista = match.group(1).strip()
            if nome_canal_lista in CANAIS_ALVO:
                lista_canais_atualizada.append(f"{linha}\n")
                
                if nome_canal_lista in novos_links:
                    lista_canais_atualizada.append(f"{novos_links[nome_canal_lista]}\n")
                else:
                    if i + 1 < len(conteudo_base):
                        lista_canais_atualizada.append(f"{conteudo_base[i+1].strip()}\n")
                        
                canais_processados.add(nome_canal_lista)
                i += 2
                continue
                
        if linha.startswith("#EXTINF") or linha.startswith("http"):
            lista_canais_atualizada.append(f"{linha}\n")
        i += 1

    for nome_canal in CANAIS_ALVO:
        if nome_canal not in canais_processados and nome_canal in novos_links:
            lista_canais_atualizada.append(f"#EXTINF:-1, {nome_canal}\n")
            lista_canais_atualizada.append(f"{novos_links[nome_canal]}\n")

    with open("lista.txt", "w", encoding="utf-8") as f:
        f.writelines(lista_canais_atualizada)
    print("👍 Sincronização com o Google Drive concluída com sucesso!")

if __name__ == "__main__":
    gerenciar_fortaleza()
