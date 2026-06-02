import os
import re
import requests
import datetime

# =====================================================================
#                      PAINEL DE CONTROLE DO COMANDANTE
# =====================================================================
# LINK DIRETO DO SEU GOOGLE DRIVE (O ROBO VAI LER DAQUI)
LINK_DRIVE_COMANDANTE = "https://drive.google.com/uc?id=1kk-OsN3R02flYm2Nl0kYZ7qI3JdzhwB_&export=download"

# REPOSITORIOS ALIADOS PARA BUSCA AUTOMÁTICA
REPOSITORIOS_ALIADOS = [
    "https://raw.githubusercontent.com/Guikiu/m3u8/main/canais.txt",
    "https://raw.githubusercontent.com/Web-Premium/IPTV/master/canais.m3u"
]

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
    print("🤖 Caçador ativo buscando fiação nos repositórios aliados...")
    
    for url_repo in REPOSITORIOS_ALIADOS:
        try:
            resposta = requests.get(url_repo, timeout=10)
            if resposta.status_code != 200:
                continue
            linhas = resposta.text.split("\n")
            
            for alvo in CANAIS_ALVO:
                if alvo in links_finais:
                    continue 
                    
                for idx, linha in enumerate(linhas):
                    if alvo.lower() in linha.lower():
                        if idx + 1 < len(linhas):
                            link_candidato = lines_finais_check = linhas[idx + 1].strip()
                            if link_candidato.startswith("http"):
                                links_finais[alvo] = link_candidato
                                break
        except Exception:
            continue
            
    return links_finais

def gerenciar_fortaleza():
    # O robô agora usa a lista do seu Drive como a base de tudo
    conteudo_base = baixar_lista_do_drive()

    # Se o Drive falhar por algum motivo, ele tenta usar a lista local para não zerar o site
    if not conteudo_base and os.path.exists("lista.txt"):
        print("⚠️ Usando lista local como segurança pois o Drive não respondeu.")
        with open("lista.txt", "r", encoding="utf-8") as f:
            conteudo_base = f.readlines()

    if not conteudo_base:
        conteudo_base = ["#EXTM3U\n"]
    
    data_atual = datetime.datetime.now().strftime("%d/%m/%Y às %H:%M")
    linha_data = f"# LISTA MANTIDA VIVA EM: {data_atual}\n"
    
    lista_canais_atualizada = []
    # Garante o cabeçalho #EXTM3U na primeira linha
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
                
        # Mantém intacto tudo o que for canal vip do seu topo
        if linha.startswith("#EXTINF") or linha.startswith("http"):
            lista_canais_atualizada.append(f"{linha}\n")
        i += 1

    # Se o robô achou canais novos que não estavam na sua lista do Drive, ele adiciona no fim
    for nome_canal in CANAIS_ALVO:
        if nome_canal not in canais_processados and nome_canal in novos_links:
            lista_canais_atualizada.append(f"#EXTINF:-1, {nome_canal}\n")
            lista_canais_atualizada.append(f"{novos_links[nome_canal]}\n")

    # Salva o resultado final no arquivo que vai para o seu site da TV
    with open("lista.txt", "w", encoding="utf-8") as f:
        f.writelines(lista_canais_atualizada)
    print("👍 Sincronização com o Google Drive concluída com sucesso!")

if __name__ == "__main__":
    gerenciar_fortaleza()
