import os
import re
import requests
import json

# =====================================================================
#                 PAINEL DE CONTROLE DO COMANDANTE
# =====================================================================

LINK_DRIVE_COMANDANTE = "https://drive.google.com/uc?id=1kk-OsN3R02flYm2Nl0kYZ7qI3JdzhwB_&export=download"
FONTE_IPTV_ORG = "https://iptv-org.github.io/iptv/index.m3u"

CANAIS_ALVO = [
    "Premiere", "Globoplay Novelas", "Gloob", "Globo SP",
    "Sportv 1", "Sportv 2", "Sportv 3", "ESPN 1", "ESPN 2",
    "PremiereFC 1", "PremiereFC 2", "PremiereFC 3", "PremiereFC 4", "PremiereFC 5",
    "Sportv 4", "ESPN 3", "ESPN 4", "BandSports", "Nosso Futebol",
    "Telecine Premium", "Telecine Action", "Telecine Touch", "Telecine Pipoca", "Telecine Fun", "Telecine Cult",
    "HBO", "HBO 2", "HBO Plus", "HBO Family", "Warner Channel", "Sony Channel", "AXN",
    "Universal TV", "Studio Universal", "TNT", "Space", "Megapix",
    "Discovery Turbo Tv", "Discovery Channel", "Discovery Home & Health", "Discovery ID",
    "National Geographic", "History Channel", "History 2", "Animal Planet", "TLC", "GNT", "Viva",
    "Gloob", "Globinho", "Disney Channel", "Cartoon Network",
    "Discovery Kids", "Nickelodeon", "Nick Jr", "Tooncast",
    "Globo SP", "Globo RJ", "Globo Minas", "Record TV", "SBT", "Band", "RedeTV"
]

def limpar_nome(texto):
    texto_limpo = re.sub(r'\s*\([^)]*\)', '', texto)
    return re.sub(r'\s+', ' ', texto_limpo).strip().lower()

def injetar_marcador_vlc(linha):
    # Se a linha começa com #EXTINF, injeta o marcador="VLC" após a duração/atributos
    if linha.startswith("#EXTINF") and 'marcador=' not in linha:
        return re.sub(r'(#EXTINF:[-\d]+)', r'\1 marcador="VLC"', linha)
    return linha

def baixar_lista_do_drive():
    print("📁 Conectando ao Google Drive do Comandante...")
    try:
        resposta = requests.get(LINK_DRIVE_COMANDANTE, timeout=15)
        if resposta.status_code == 200:
            print("👍 Lista do Drive baixada com sucesso!")
            return resposta.text.splitlines()
        return []
    except Exception as e:
        print(f"❌ Falha na conexão com o Drive: {e}")
        return []

def caçar_links_iptv_org():
    links_finais = {}
    print("🤖 Caçador de alta precisão ativo...")
    try:
        resposta = requests.get(FONTE_IPTV_ORG, timeout=20)
        linhas = resposta.text.splitlines()
        
        for idx, linha in enumerate(linhas):
            if linha.startswith("#EXTINF"):
                match_git = re.search(r',(.+)$', linha)
                if not match_git: continue
                nome_git = match_git.group(1).strip().lower()

                for alvo in CANAIS_ALVO:
                    if alvo in links_finais: continue
                    
                    if re.search(rf'\b{re.escape(alvo.lower())}\b', nome_git):
                        if any(x in nome_git for x in ["boxing", "test", "promo"]): continue
                        
                        if idx + 1 < len(linhas):
                            link = linhas[idx + 1].strip()
                            if link.startswith("http"):
                                links_finais[alvo] = {
                                    "link": link,
                                    "extinf_original": injetar_marcador_vlc(linha)
                                }
                                print(f"🎯 [ACHADO] Canal {alvo} pescado: {nome_git}")
                                break
    except Exception as e:
        print(f"❌ Erro na caçada: {e}")
    return links_finais

def gerenciar_fortaleza():
    conteudo_base = baixar_lista_do_drive()
    if not conteudo_base and os.path.exists("lista.txt"):
        print("⚠️ Usando lista local como segurança.")
        with open("lista.txt", "r", encoding="utf-8") as f:
            conteudo_base = f.read().splitlines()

    if not conteudo_base: return
    
    novos_links = caçar_links_iptv_org()
    lista_canais_atualizada = []
    
    i = 0
    while i < len(conteudo_base):
        linha = conteudo_base[i].strip()
        if not linha:
            lista_canais_atualizada.append("\n"); i += 1; continue
        if linha.upper().startswith("IMG="):
            lista_canais_atualizada.append(f"{linha}\n"); i += 1; continue

        if linha.startswith("#EXTINF"):
            match = re.search(r'#EXTINF:.*,\s*(.*)', linha)
            canal = match.group(1).strip() if match else ""
            
            if canal in CANAIS_ALVO:
                # Injeta o marcador na linha existente do Drive/base
                lista_canais_atualizada.append(f"{injetar_marcador_vlc(linha)}\n")
                
                if canal in novos_links:
                    lista_canais_atualizada.append(f"{novos_links[canal]['link']}\n")
                    i += 2
                    continue
                else:
                    if i + 1 < len(conteudo_base): 
                        lista_canais_atualizada.append(f"{conteudo_base[i+1].strip()}\n")
                    i += 2
                    continue

        lista_canais_atualizada.append(f"{injetar_marcador_vlc(linha)}\n")
        i += 1

    with open("lista.txt", "w", encoding="utf-8") as f: 
        f.writelines(lista_canais_atualizada)
    
    bussola = {"url_lista": "https://raw.githubusercontent.com/cloneey9090-netizen/tv/refs/heads/main/lista.txt"}
    with open("config.json", "w", encoding="utf-8") as f_json:
        json.dump(bussola, f_json, indent=4)
        
    print("👍 Sincronização concluída com a estrutura original e marcador VLC!")

if __name__ == "__main__":
    gerenciar_fortaleza()
