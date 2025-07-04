import time
import random
import csv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException

# Configurações
MAX_CLICKS = 80
CSV_FILE = 'imoveis_quinto_andar_coletados.csv'
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"

# Configurar o driver
options = webdriver.ChromeOptions()
options.add_argument(f'user-agent={USER_AGENT}')
options.add_argument('--disable-blink-features=AutomationControlled')
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option('useAutomationExtension', False)
options.add_argument('--start-maximized')

driver = webdriver.Chrome(options=options)
driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

# Acessar o site
driver.get('https://www.quintoandar.com.br/alugar/imovel/pinheiros-sao-paulo-sp-brasil?flexible=true&referrer=profilingv2')

# Aceitar cookies
try:
    cookie_btn = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, '//button[contains(text(), "Aceitar todos os cookies")]'))
    )
    cookie_btn.click()
    time.sleep(2)
except (NoSuchElementException, TimeoutException):
    pass


def coletar_urls():
    urls = []
    try:
        containers = driver.find_elements(By.CSS_SELECTOR, 'div[data-testid="house-card-container-rent"]')

        for container in containers:
            try:
                link = container.find_element(By.CSS_SELECTOR, 'a.StyledLink_styledLink__P_6FN')
                url = link.get_attribute('href')

                if url:
                    if not url.startswith('http'):
                        url = f'https://www.quintoandar.com.br{url}'
                    # Garante que a URL completa fique em uma única célula
                    urls.append({'url': url.split('?')[0]})
            except Exception as e:
                print(f"Erro ao processar card: {e}")
                continue
    except Exception as e:
        print(f"Erro ao encontrar containers: {e}")

    return urls


# Coletar dados
todos_imoveis = []
urls_coletadas = set()

for click_count in range(MAX_CLICKS):
    print(f"Coletando URLs (clique {click_count + 1}/{MAX_CLICKS})...")

    novos_imoveis = coletar_urls()

    for imovel in novos_imoveis:
        if imovel['url'] not in urls_coletadas:
            todos_imoveis.append(imovel)
            urls_coletadas.add(imovel['url'])
            print(f"Adicionado: {imovel['url']}")

    # Tentar clicar no botão "Ver mais"
    try:
        ver_mais = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//button[contains(text(), "Ver mais")]'))
        )
        driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", ver_mais)
        time.sleep(random.uniform(1, 2))
        ver_mais.click()
        time.sleep(random.uniform(3, 5))
    except (TimeoutException, NoSuchElementException):
        print("Botão 'Ver mais' não encontrado. Fazendo scroll manual...")
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(random.uniform(3, 5))

        if len(coletar_urls()) <= len(todos_imoveis):
            print("Não há mais URLs para carregar.")
            break

# Correção principal: Configuração do CSV para evitar divisão das URLs
with open(CSV_FILE, mode='w', newline='', encoding='utf-8') as file:
    writer = csv.writer(file)
    writer.writerow(['url'])  # Cabeçalho
    for imovel in todos_imoveis:
        # Escreve cada URL em uma linha, garantindo que fique em uma única célula
        writer.writerow([imovel['url']])

print(f"\n✅ URLs salvas corretamente em {CSV_FILE}")
print(f"Total de URLs coletadas: {len(todos_imoveis)}")

driver.quit()