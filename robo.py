import os
import re
import requests
import json

# =====================================================================
#                 PAINEL DE CONTROLE DO COMANDANTE
# =====================================================================

#LINK_DRIVE_COMANDANTE = "https://drive.google.com/uc?id=1kk-OsN3R02flYm2Nl0kYZ7qI3JdzhwB_&export=download"
FONTE_IPTV_ORG = "https://iptv-org.github.io/iptv/index.m3u"

CANAIS_ALVO = [
    "PremiereFC 1", "PremiereFC 2", "PremiereFC 3", "PremiereFC 4", "PremiereFC 5",
    "Sportv 1", "Sportv 2", "Sportv 3", "Sportv 4", "ESPN 1", "ESPN 2", "ESPN 3", "ESPN 4",
    "BandSports", "Nosso Futebol",
    "Telecine Premium", "Telecine Action", "Telecine Touch", "Telecine Pipoca", "Telecine Fun", "Telecine Cult",
    "HBO", "HBO 2", "HBO Plus", "HBO Family", "Warner Channel", "Sony Channel", "AXN",
    "Universal TV", "Studio Universal", "TNT", "Space", "Megapix",
    "Discovery Turbo Tv", "Discovery Channel", "Discovery Home & Health", "Discovery ID",
    "National Geographic", "History Channel", "History 2", "Animal Planet", "TLC", "GNT", "Viva",
    "Globoplay Novelas",
    "Gloob (1080)", "Globinho (1080)", "Disney Channel (1080)", "Cartoon Network (1080)",
    "Discovery Kids (1080)", "Nickelodeon (1080)", "Nick Jr (1080)", "Tooncast (1080)",
    "Globo SP", "Globo RJ", "Globo Minas", "Record TV", "SBT", "Band", "RedeTV"
]

def baixar_lista_do_drive():
    print("📁 Conectando ao Google Drive do Comandante...")
    try:
        resposta = requests.get(LINK_DRIVE_COMANDANTE, timeout=15)
        return resposta.text.splitlines() if resposta.status_code == 200 else []
    except: return []

def caçar_links_iptv_org():
    links_finais = {}
    print("🤖 Caçador de alta precisão ativo...")
    try:
        resposta = requests.get(FONTE_IPTV_ORG, timeout=20)
        linhas = resposta.text.splitlines()
        
        # Lista dos alvos que AINDA não pescamos
        nao_pescados = [a for a in CANAIS_ALVO]
        
        for idx, linha in enumerate(linhas):
            if linha.startswith("#EXTINF"):
                match_github = re.search(r',(.+)$', linha)
                if not match_github: continue
                nome_github = match_github.group(1).strip().lower()

                for alvo in nao_pescados:
                    alvo_norm = re.sub(r'\(.*?\)', '', alvo).strip().lower()
                    
                    # Comparação super flexível
                    if alvo_norm in nome_github or (alvo_norm.replace(" ", "") in nome_github.replace(" ", "")):
                        if idx + 1 < len(linhas):
                            link = linhas[idx + 1].strip()
                            if link.startswith("http"):
                                logo = ""
                                match_logo = re.search(r'tvg-logo="([^"]+)"', linha)
                                if match_logo: logo = match_logo.group(1).strip()
                                
                                links_finais[alvo] = {"video": link, "logo": logo}
                                print(f"🎯 [PESCADO] {alvo} -> ({nome_github})")
                                nao_pescados.remove(alvo)
                                break
        
        # 🚨 RELATÓRIO DE MISSÃO (O que o robô não achou)
        if nao_pescados:
            print("\n⚠️ CANAIS NÃO ENCONTRADOS NO REPOSITÓRIO:")
            for item in nao_pescados:
                print(f"❌ {item}")
            print("💡 Dica: Verifique se estes nomes existem no iptv-org.")
            
    except Exception as e: print(f"❌ Erro: {e}")
    return links_finais

def gerenciar_fortaleza():
    conteudo_base = baixar_lista_do_drive()
    if not conteudo_base and os.path.exists("lista.txt"):
        with open("lista.txt", "r", encoding="utf-8") as f: conteudo_base = f.read().splitlines()

    if not conteudo_base: return
    
    novos_dados = caçar_links_iptv_org()
    lista_canais_atualizada = []
    
    i = 0
    while i < len(conteudo_base):
        linha = conteudo_base[i].strip()
        if not linha:
            lista_canais_atualizada.append("\n"); i += 1; continue
        if linha.upper().startswith("IMG="):
            lista_canais_atualizada.append(f"{linha}\n"); i += 1; continue

        if linha.startswith("#EXTINF"):
            if ", AUTO" in linha or ",AUTO" in linha:
                lista_canais_atualizada.append(f"{linha}\n")
                if i + 1 < len(conteudo_base): lista_canais_atualizada.append(f"{conteudo_base[i+1].strip()}\n")
                i += 2; continue
            
            match = re.search(r'#EXTINF:.*,\s*(.*)', linha)
            if match:
                nome_canal = match.group(1).strip()
                if nome_canal in CANAIS_ALVO and nome_canal in novos_dados:
                    dados = novos_dados[nome_canal]
                    logo_str = f' tvg-logo="{dados["logo"]}"' if dados["logo"] else ''
                    lista_canais_atualizada.append(f'#EXTINF:-1{logo_str},{nome_canal}\n')
                    lista_canais_atualizada.append(f"{dados['video']}\n")
                    i += 2; continue

        lista_canais_atualizada.append(f"{linha}\n")
        i += 1

    with open("lista.txt", "w", encoding="utf-8") as f: f.writelines(lista_canais_atualizada)
        
    bussola = {"url_lista": "https://raw.githubusercontent.com/cloneey9090-netizen/tv/refs/heads/main/lista.txt"}
    with open("config.json", "w", encoding="utf-8") as f_json: json.dump(bussola, f_json, indent=4)
    print("👍 Sincronização automática e LOGOS injetadas com sucesso!")

if __name__ == "__main__":
    gerenciar_fortaleza()
