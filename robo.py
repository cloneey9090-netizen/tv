import os
import re
import requests
import datetime
import json

# =====================================================================
#                 PAINEL DE CONTROLE DO COMANDANTE
# =====================================================================

# LINK DIRETO DO SEU GOOGLE DRIVE (O ROBO VAI LER DAQUI COMO ORDEM FINAL)
LINK_DRIVE_COMANDANTE = "https://drive.google.com/uc?id=1kk-OsN3R02flYm2Nl0kYZ7qI3JdzhwB_&export=download"

# A MINA DE OURO QUE VOCÊ ACHOU (IPTV-ORG) - FONTE AUTOMÁTICA PRINCIPAL
FONTE_IPTV_ORG = "https://iptv-org.github.io/iptv/index.m3u"

# CANAIS QUE O ROBÔ VAI VALIDAR OU CAÇAR AUTOMATICAMENTE
CANAIS_ALVO = [
    # ⚽ Esportes (Expandido)
    "PremiereFC 1",
    "PremiereFC 2",
    "PremiereFC 3",
    "PremiereFC 4",
    "PremiereFC 5",
    "Sportv 1",
    "Sportv 2",
    "Sportv 3",
    "Sportv 4",
    "ESPN 1",
    "ESPN 2",
    "ESPN 3",
    "ESPN 4",
    "BandSports",
    "Nosso Futebol",

    # 🎬 Filmes e Séries
    "Telecine Premium",
    "Telecine Action",
    "Telecine Touch",
    "Telecine Pipoca",
    "Telecine Fun",
    "Telecine Cult",
    "HBO",
    "HBO 2",
    "HBO Plus",
    "HBO Family",
    "Warner Channel",
    "Sony Channel",
    "AXN",
    "Universal TV",
    "Studio Universal",
    "TNT",
    "Space",
    "Megapix",

    # 🧪 Documentários e Variedades
    "Discovery Turbo Tv",
    "Discovery Channel",
    "Discovery Home & Health",
    "Discovery ID",
    "National Geographic",
    "History Channel",
    "History 2",
    "Animal Planet",
    "TLC",
    "GNT",
    "Viva",
    "Globoplay Novelas",

    # 👶 Infantis (1080p)
    "Gloob (1080)",
    "Globinho (1080)",
    "Disney Channel (1080)",
    "Cartoon Network (1080)",
    "Discovery Kids (1080)",
    "Nickelodeon (1080)",
    "Nick Jr (1080)",
    "Tooncast (1080)",

    # 📺 Abertos / Premium Locais
    "Globo SP",
    "Globo RJ",
    "Globo Minas",
    "Record TV",
    "SBT",
    "Band",
    "RedeTV"
]
# =====================================================================

def baixar_lista_do_drive():
    print("📁 Conectando ao Google Drive do Comandante...")
    try:
        resposta = requests.get(LINK_DRIVE_COMANDANTE, timeout=15)
        if resposta.status_code == 200:
            print("👍 Lista do Drive baixada com sucesso!")
            return resposta.text.splitlines()
        else:
            print(f"❌ Erro ao acessar o Drive (Status: {resposta.status_code})")
            return []
    except Exception as e:
        print(f"❌ Falha na conexão com o Drive: {e}")
        return []

def caçar_links_iptv_org():
    links_finais = {}
    print("🤖 Caçador ativo sugando a fiação principal do iptv-org...")
    
    try:
        resposta = requests.get(FONTE_IPTV_ORG, timeout=20)
        if resposta.status_code != 200:
            print("❌ Não foi possível acessar o link do iptv-org.")
            return links_finais
            
        linhas = resposta.text.splitlines()
        
        # Varre a lista gigante procurando nossos alvos
        for idx, linha in enumerate(linhas):
            if linha.startswith("#EXTINF"):
                # Verifica se a linha pertence ao Brasil ou tem a marca que queremos
                for alvo in CANAIS_ALVO:
                    if alvo in links_finais:
                        continue  # Se já achou esse canal, pula pro próximo
                    
                    # O pulo do gato: procura o nome do canal no fim da linha ou nas tags
                    if alvo.lower() in linha.lower():
                        if idx + 1 < len(linhas):
                            link_candidato = linhas[idx + 1].strip()
                            if link_candidato.startswith("http"):
                                links_finais[alvo] = link_candidato
                                print(f"🎯 [ACHADO] Canal {alvo} pescado com sucesso!")
                                break
    except Exception as e:
        print(f"❌ Erro durante a caçada no iptv-org: {e}")
        
    return links_finais

def gerenciar_fortaleza():
    conteudo_base = baixar_lista_do_drive()

    if not conteudo_base and os.path.exists("lista.txt"):
        print("⚠️ Usando lista local como segurança pois o Drive não respondeu.")
        with open("lista.txt", "r", encoding="utf-8") as f:
            conteudo_base = f.read().splitlines()

    if not conteudo_base:
        print("❌ Sem dados para processar.")
        return
    
    # Executa a busca na nova fonte que você descobriu
    novos_links = caçar_links_iptv_org()
    lista_canais_atualizada = []
    
    i = 0
    while i < len(conteudo_base):
        linha = conteudo_base[i].strip()
        
        # 1. Preserva linhas vazias
        if not linha:
            lista_canais_atualizada.append("\n")
            i += 1
            continue
            
        # 2. Mantém os Banners/Imagens intactos
        if linha.upper().startswith("IMG="):
            lista_canais_atualizada.append(f"{linha}\n")
            i += 1
            continue

        # 3. Processamento inteligente dos blocos
        if linha.startswith("#EXTINF"):
            if ", AUTO" in linha or ",AUTO" in linha:
                lista_canais_atualizada.append(f"{linha}\n")
                if i + 1 < len(conteudo_base):
                    lista_canais_atualizada.append(f"{conteudo_base[i+1].strip()}\n")
                i += 2
                continue
            
            # Captura o nome do canal que está na sua lista padrão
            match = re.search(r'#EXTINF:.*,\s*(.*)', linha)
            if match:
                nome_canal_lista = match.group(1).strip()
                
                if nome_canal_lista in CANAIS_ALVO:
                    lista_canais_atualizada.append(f"{linha}\n")
                    # Se o caçador achou o link updated no iptv-org, coloca ele!
                    if nome_canal_lista in novos_links:
                        lista_canais_atualizada.append(f"{novos_links[nome_canal_lista]}\n")
                    else:
                        # Se não achou, mantém o link que já estava antes para não ficar preto
                        if i + 1 < len(conteudo_base):
                            lista_canais_atualizada.append(f"{conteudo_base[i+1].strip()}\n")
                    i += 2
                    continue

        # 4. Mantém o resto intacto
        lista_canais_atualizada.append(f"{linha}\n")
        i += 1

    # Salva o arquivo final limpo
    with open("lista.txt", "w", encoding="utf-8") as f:
        f.writelines(lista_canais_atualizada)
        
    # --- A BÚSSOLA ---
    bussola = {
        "url_lista": "https://raw.githubusercontent.com/cloneey9090-netizen/tv/refs/heads/main/lista.txt"
    }
    with open("config.json", "w", encoding="utf-8") as f_json:
        json.dump(bussola, f_json, indent=4)
        
    print("👍 Sincronização automática e Bússola calibradas com o iptv-org!")

if __name__ == "__main__":
    gerenciar_fortaleza()
