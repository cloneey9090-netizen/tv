import os
import re
import requests
import json

# =====================================================================
#                PAINEL DE CONTROLE DO COMANDANTE
# =====================================================================

LINK_DRIVE_COMANDANTE = "https://drive.google.com/uc?id=1kk-OsN3R02flYm2Nl0kYZ7qI3JdzhwB_&export=download"
FONTE_IPTV_ORG = "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/br.m3u"
PASTA_DESTINO = "resultado"

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
    # Se já tem #EXTINF, insere o marcador="VLC" logo após a duração/atributos iniciais
    if linha.startswith("#EXTINF"):
        if 'marcador=' not in linha:
            # Substitui #EXTINF:duracao por #EXTINF:duracao marcador="VLC"
            return re.sub(r'(#EXTINF:[-\d]+)', r'\1 marcador="VLC"', linha)
    return linha

def testar_link_ativo(url):
    try:
        resposta = requests.head(url, timeout=4, allow_redirects=True)
        if resposta.status_code < 400:
            return True
        resp_get = requests.get(url, timeout=3, stream=True)
        if resp_get.status_code < 400:
            resp_get.close()
            return True
    except:
        pass
    return False

def baixar_lista_do_drive():
    print("A ligar ao Google Drive do Comandante...")
    try:
        resposta = requests.get(LINK_DRIVE_COMANDANTE, timeout=15)
        if resposta.status_code == 200:
            print("Lista do Drive descarregada com sucesso!")
            return resposta.text.splitlines()
        else:
            print(f"Erro ao aceder ao Drive (Estado: {resposta.status_code})")
            return []
    except Exception as e:
        print(f"Falha na ligação com o Drive: {e}")
        return []

def caçar_links_iptv_org():
    links_finais = {}
    print("Caçador focado no repositório mestre com Teste de Pulso (Modo Amplo)...")
    try:
        resposta = requests.get(FONTE_IPTV_ORG, timeout=20)
        if resposta.status_code != 200:
            print(f"❌ Erro ao aceder à fonte mestre (Estado: {resposta.status_code})")
            return links_finais
            
        linhas = resposta.text.splitlines()
        for idx, linha in enumerate(linhas):
            if linha.startswith("#EXTINF"):
                match = re.search(r',(.+)$', linha)
                if not match: continue
                nome_bruto_git = match.group(1).strip()
                nome_limpo_git = limpar_nome(nome_bruto_git)
                
                for alvo in CANAIS_ALVO:
                    if alvo in links_finais: continue
                    alvo_limpo = limpar_nome(alvo)
                    
                    match_exato = False
                    if alvo_limpo == "viva":
                        if nome_limpo_git == "viva":
                            match_exato = True
                    else:
                        if alvo_limpo == nome_limpo_git or (len(alvo_limpo) > 3 and alvo_limpo in nome_limpo_git):
                            match_exato = True
                            
                    if match_exato:
                        if idx + 1 < len(linhas):
                            link_candidato = linhas[idx + 1].strip()
                            if link_candidato.startswith("http"):
                                print(f"[TESTANDO] Pulso de {alvo}...")
                                if testar_link_ativo(link_candidato):
                                    links_finais[alvo] = {
                                        "link": link_candidato,
                                        "extinf_original": injetar_marcador_vlc(linha),
                                        "nome_bruto": nome_bruto_git
                                    }
                                    print(f"✅ [VALIDADO] Canal {alvo} operacional: {nome_bruto_git}")
                                else:
                                    print(f"⚠️ [MORTO] Link de {alvo} sem resposta, ignorado.")
                                break
    except Exception as e:
        print(f"Erro durante a caçada nacional: {e}")
    return links_finais

def gerenciar_fortaleza():
    os.makedirs(PASTA_DESTINO, exist_ok=True)
    
    conteudo_base = baixar_lista_do_drive()
    if not conteudo_base and os.path.exists("lista.txt"):
        print("A usar a lista local de segurança.")
        with open("lista.txt", "r", encoding="utf-8") as f:
            conteudo_base = f.read().splitlines()

    if not conteudo_base:
        print("Sem dados para processar.")
        return
    
    novos_links = caçar_links_iptv_org()
    lista_canais_atualizada = []
    canais_encontrados_na_base = set()
    
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
                lista_canais_atualizada.append(f"{injetar_marcador_vlc(linha)}\n")
                if i + 1 < len(conteudo_base):
                    lista_canais_atualizada.append(f"{conteudo_base[i+1].strip()}\n")
                i += 2
                continue
            
            match = re.search(r'#EXTINF:.*,\s*(.*)', linha)
            if match:
                nome_canal_lista = match.group(1).strip()
                if nome_canal_lista in CANAIS_ALVO:
                    canais_encontrados_na_base.add(nome_canal_lista)
                    lista_canais_atualizada.append(f"{injetar_marcador_vlc(linha)}\n")
                    if nome_canal_lista in novos_links:
                        lista_canais_atualizada.append(f"{novos_links[nome_canal_lista]['link']}\n")
                    else:
                        if i + 1 < len(conteudo_base):
                            lista_canais_atualizada.append(f"{conteudo_base[i+1].strip()}\n")
                    i += 2
                    continue

        lista_canais_atualizada.append(f"{linha}\n")
        i += 1

    # Adiciona no final os canais validados que o caçador achou na fonte, mas que NÃO estavam na sua base
    adicionados_novos = 0
    for canal, dados in novos_links.items():
        if canal not in canais_encontrados_na_base:
            lista_canais_atualizada.append(f"\n{dados['extinf_original']}\n")
            lista_canais_atualizada.append(f"{dados['link']}\n")
            adicionados_novos += 1
            print(f"➕ [ADICIONADO] Novo canal anexado à lista: {canal}")

    caminho_arquivo_final = os.path.join(PASTA_DESTINO, "lista.txt")
    with open(caminho_arquivo_final, "w", encoding="utf-8") as f:
        f.writelines(lista_canais_atualizada)
        
    print(f"Sincronização concluída! {adicionados_novos} novos canais adicionados. Salvo em: {caminho_arquivo_final}")

if __name__ == "__main__":
    gerenciar_fortaleza()
