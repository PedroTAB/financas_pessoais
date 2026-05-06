# scripts/add_user.py
"""Script CLI para cadastrar usuários."""
import bcrypt
import yaml
from pathlib import Path


def main():
    print("👤 **CADASTRO DE USUÁRIO**\n")
    
    username = input("Username (sem espaços): ").strip()
    if not username:
        print("❌ Username obrigatório")
        return
    
    name = input("Nome completo: ").strip()
    if not name:
        print("❌ Nome completo obrigatório")
        return
    
    password = input("Senha: ").strip()
    if len(password) < 6:
        print("❌ Senha deve ter pelo menos 6 caracteres")
        return
    
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    cfg_file = Path("auth_config.yaml")
    if cfg_file.exists():
        with open(cfg_file) as f:
            config = yaml.safe_load(f)
    else:
        config = {
            "credentials": {"usernames": {}},
            "cookie": {
                "name": "fin_auth",
                "key": "GERE_UMA_CHAVE_FORTE_AQUI_32_CARACTERES",  # python -c "import secrets; print(secrets.token_hex(32))"
                "expiry_days": 30,
            },
        }

    if username in config["credentials"]["usernames"]:
        print(f"⚠️  Usuário '{username}' já existe.")
        return

    config["credentials"]["usernames"][username] = {
        "name": name,
        "password": hashed
    }
    
    with open(cfg_file, "w") as f:
        yaml.dump(config, f, allow_unicode=True, default_flow_style=False, indent=2)
    
    print(f"\n✅ **Usuário '{username}' ({name}) criado com sucesso!**")
    print(f"💾 Arquivo: auth_config.yaml")
    print("\n🔐 **ADICIONE auth_config.yaml ao .gitignore**")


if __name__ == "__main__":
    main()