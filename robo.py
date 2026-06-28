import os
import re
import requests
import datetime
import json

# =====================================================================
#                 PAINEL DE CONTROLE DO COMANDANTE
# =====================================================================

LINK_DRIVE_COMANDANTE = "https://drive.google.com/uc?id=1kk-OsN3R02flYm2Nl0kYZ7qI3JdzhwB_&export=download"
FONTE_IPTV_ORG = "https://iptv-org.github.io/iptv/index.m3u"

CANAIS_ALVO = [
    # ⚽ Esportes (Expandido)
    "PremiereFC 1", "PremiereFC 2", "PremiereFC 3", "PremiereFC 4", "PremiereFC 5",
    "Sportv 1", "Sportv 2", "Sportv 3", "Sportv 4", "ESPN 1", "ESPN 2", "ESPN 3", "ESPN 4",
    "BandSports", "Nosso Futebol",

    # 🎬 Filmes e Séries
    "Telecine Premium", "Telecine Action", "Telecine Touch", "Telecine Pipoca", "Telecine Fun", "Telecine Cult",
    "HBO", "HBO 2", "HBO Plus", "HBO Family", "Warner Channel", "Sony Channel", "AXN",
    "Universal TV", "Studio Universal", "TNT", "Space", "Megapix",

    # 🧪 Documentários e Variedades
    "Discovery Turbo Tv", "Discovery Channel", "Discovery Home & Health", "Discovery ID",
    "National Geographic", "History Channel", "History 2", "Animal Planet", "TLC", "GNT", "Viva",
    "Globoplay Novelas",

    # 👶 Infantis (1080p)
    "Gloob (1080)", "Globinho (1080)", "Disney Channel (1080)", "Cartoon Network (1080)",
    "Discovery Kids (1080)", "Nickelodeon (1080)", "Nick Jr (1080)", "Tooncast (1080)",

    # 📺 Abertos / Premium Locais
    "Globo SP", "Globo RJ", "Globo Minas", "Record TV", "SBT", "Band", "RedeTV"
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
    print("🤖 Caçador inteligente e coletor de logos ativo...")
    
    try:
        resposta = requests.get(FONTE_IPTV_ORG, timeout=20)
        if resposta.status_code != 200:
            print("❌ Não foi possível acessar o link do iptv-org.")
            return links_finais
            
        linhas = resposta.text.splitlines()
        
        for idx, linha in enumerate(linhas):
            if linha.startswith("#EXTINF"):
                for alvo in CANAIS_ALVO:
                    if alvo in links_finais:
                        continue
                    
                    alvo_limpo = re.sub(r'\(.*?\)', '', alvo).strip().lower()
                    alvo_limpo = alvo_limpo.replace(" sp", "").replace(" rj", "").replace(" minas", "")
                    
                    nome_linha_iptv = linha.lower()
                    
                    if alvo_limpo in nome_linha_iptv:
                        if idx + 1 < len(linhas):
                            link_candidato = linhas[idx + 1].strip()
                            if link_candidato.startswith("http"):
                                # 🔥 EXTRAÇÃO DA LOGO: Procura a tag tvg-logo="URL"
                                logo_link = ""
                                match_logo = re.search(r'tvg-logo="([^"]+)"', linha)
                                if match_logo:
                                    logo_link = match_logo.group(1).strip()
                                
                                # Guarda o link do vídeo e a logo juntos para esse canal
                                links_finais[alvo] = {
                                    "video": link_candidato,
                                    "logo": logo_link
                                }
                                print(f"🎯 [PESCADO + LOGO] {alvo} localizado!")
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
    
    novos_dados = caçar_links_iptv_org()
    lista_canais_atualizada = []
    
    i = 0
    while i < len(conteudo_base):
        linha = conteudo_base[i].strip()
        
        if not linha:
            lista_canais_atualizada.append("\n")
            i += 1
            continue
            
        if linha.upper().startswith("IMG="):
            lista_canais_atualizada.append(f"{linha}\n")
            i += 1
            continue

        if linha.startswith("#EXTINF"):
            if ", AUTO" in linha or ",AUTO" in linha:
                lista_canais_atualizada.append(f"{linha}\n")
                if i + 1 < len(conteudo_base):
                    lista_canais_atualizada.append(f"{conteudo_base[i+1].strip()}\n")
                i += 2
                continue
            
            match = re.search(r'#EXTINF:.*,\s*(.*)', linha)
            if match:
                nome_canal_lista = match.group(1).strip()
                
                if nome_canal_lista in CANAIS_ALVO:
                    # Se o caçador achou dados novos no github do iptv-org...
                    if nome_canal_lista in novos_dados:
                        dados_canal = novos_dados[nome_canal_lista]
                        
                        # 🔄 RECONSTRUÇÃO DA LINHA DA LOGO: 
                        # Se achou uma logo lá, coloca. Se não, deixa em branco pra não quebrar
                        logo_str = f' tvg-logo="{dados_canal["logo"]}"' if dados_canal["logo"] else ''
                        
                        lista_canais_atualizada.append(f'#EXTINF:-1{logo_str},{nome_canal_lista}\n')
                        lista_canais_atualizada.append(f"{dados_canal['video']}\n")
                    else:
                        # Se não achou na busca, mantém exatamente o bloco original do seu drive
                        lista_canais_atualizada.append(f"{linha}\n")
                        if i + 1 < len(conteudo_base):
                            lista_canais_atualizada.append(f"{conteudo_base[i+1].strip()}\n")
                    i += 2
                    continue

        lista_canais_atualizada.append(f"{linha}\n")
        i += 1

    with open("lista.txt", "w", encoding="utf-8") as f:
        f.writelines(lista_canais_atualizada)
        
    bussola = {
        "url_lista": "https://raw.githubusercontent.com/cloneey9090-netizen/tv/refs/heads/main/lista.txt"
    }
    with open("config.json", "w", encoding="utf-8") as f_json:
        json.dump(bussola, f_json, indent=4)
        
    print("👍 Sincronização automática e LOGOS injetadas com sucesso!")

if __name__ == "__main__":
    gerenciar_fortaleza()
