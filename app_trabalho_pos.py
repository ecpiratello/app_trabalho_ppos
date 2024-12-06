from openai import OpenAI
from dotenv import load_dotenv
from guardrails.hub import ValidJson
from guardrails import Guard
import os

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()

# Configurar a chave da API da OpenAI
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("A chave da API 'OPENAI_API_KEY' não foi encontrada. Verifique o arquivo .env.")

# Inicializar o cliente da OpenAI
client = OpenAI(api_key=api_key)

# Configurar o Guardrails com o validador ValidJson
guard = Guard().use(ValidJson, on_fail="exception")

def generate_json_file_with_llm(file_path):
    """
    Gera um arquivo JSON fictício diretamente utilizando a LLM.
    """
    prompt = """
    Gere um JSON contendo exatamente 100 objetos em uma lista. 
    Não inclua explicações, formatações extras ou aspas adicionais.
    O JSON deve seguir o seguinte formato:
    [
        {
            "data": "DD-MM-YYYY",
            "produto": "Cimento|Areia|Bloco de Concreto|Tijolo|Reboco",
            "quantidade": inteiro entre 10 e 200,
            "preco_unitario": inteiro entre 5 e 50,
            "margem líquida": percentual entre 0 e 100,
            "valor_total": quantidade * preco_unitario
        },
        ...
    ]
    Para todos os registros, siga as regras definidas acima.
    """
    try:
        # Obter a resposta da LLM
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": "Você é um assistente que retorna dados formatados corretamente."},
                      {"role": "user", "content": prompt}]
        ).choices[0].message.content.strip()

        # Forçar um erro de formato no registro 5
        #response_split = response.splitlines()
        #for i, line in enumerate(response_split):
        #    if "\"produto\":" in line and i >= 5:  # Localiza o registro 5 pelo índice
        #        response_split[i] = line.replace(",", ",,,,")  # Introduz erro ao adicionar vírgulas extras
        #        break
        #response = "\n".join(response_split)

        # Salvar o JSON como string
        with open(file_path, "w", encoding="utf-8") as file:
            file.write(response)
        print(f"Arquivo JSON gerado em: {file_path}")

    except Exception as e:
        raise RuntimeError(f"Erro ao gerar o arquivo JSON com a LLM: {e}")

def validate_json_file_with_guardrails(file_path):
    """
    Lê e valida o arquivo JSON utilizando apenas o Guardrails.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            json_content = file.read()

        # Validar o JSON completo com Guardrails
        try:
            guard.validate(json_content)
            print("JSON validado com sucesso!")
            return True
        except Exception as e:
            print("Erro na validação do JSON:")
            print(f"{e}")
            return False

    except Exception as e:
        print(f"Erro ao validar o arquivo JSON: {e}")
        return False

def ask_questions_about_json(llm_client, file_path):
    """
    Permite que o usuário faça perguntas sobre o conteúdo do JSON.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            json_content = file.read()

        print("\nFaça perguntas sobre o JSON (digite 'sair' para encerrar):")
        while True:
            user_question = input("Pergunta: ")
            if user_question.lower() == "sair":
                print("Encerrando análise.")
                break

            prompt = f"""
            Aqui está o conteúdo de um JSON: {json_content}.
            Responda à seguinte pergunta com base exclusivamente no JSON fornecido. 
            Não responda nehuma pergunta que não tenha relação com o conteúdo do JSON.
            Caso uma pergunta fora deste contexto seja feita, responda "Só respondo 
            perguntas sobre o arquivo de vendas": {user_question}
            """
            try:
                # Obter a resposta da LLM
                response = llm_client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "system", "content": "Você é um assistente que analisa e responde com base em JSON. Você responde as perguntas em formato de texto corrido e não utiliza o formato JSON nas respostas"},
                              {"role": "user", "content": prompt}]
                ).choices[0].message.content.strip()
                print(f"Resposta: {response}")
            except Exception as e:
                print(f"Erro ao processar a pergunta: {e}")

    except Exception as e:
        print(f"Erro ao carregar o arquivo JSON para perguntas: {e}")

# Caminho para salvar o arquivo JSON gerado
file_path = "vendas_geradas_llm.json"

# Gerar, validar o JSON e permitir análise
try:
    generate_json_file_with_llm(file_path)
    is_valid = validate_json_file_with_guardrails(file_path)
    if is_valid:
        ask_questions_about_json(client, file_path)
    else:
        print("Não é possível fazer perguntas porque o JSON é inválido.")
except Exception as e:
    print(f"Erro geral: {e}")
