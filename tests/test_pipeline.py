"""
Testes unitários para validação do pipeline CI/CD
"""
import os
import sys
import json

def test_presets_valid():
    """Testa se o arquivo de presets é um JSON válido"""
    preset_path = os.path.join(os.path.dirname(__file__), '..', 'configs', 'presets.json')
    
    try:
        with open(preset_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        assert isinstance(data, dict), "Presets deve ser um dicionário"
        
        # Verifica se existe a chave 'presets' ou se os presets estão na raiz
        if 'presets' in data:
            presets_data = data['presets']
        else:
            presets_data = data
        
        assert isinstance(presets_data, dict), "Presets deve ser um dicionário"
        assert len(presets_data) > 0, "Presets não pode estar vazio"
        
        # Valida estrutura de cada preset
        for key, value in presets_data.items():
            assert isinstance(value, dict), f"Preset '{key}' deve ser um dicionário"
            assert 'gpu_layers' in value, f"Preset '{key}' falta 'gpu_layers'"
            assert 'quantization' in value or 'model_quantization' in value, f"Preset '{key}' falta 'quantization'"
            assert isinstance(value['gpu_layers'], int), f"'gpu_layers' em '{key}' deve ser inteiro"
            assert value['gpu_layers'] >= 0, f"'gpu_layers' em '{key}' deve ser >= 0"
        
        print("✓ Teste de presets passou")
        return True
        
    except json.JSONDecodeError as e:
        print(f"✗ Erro: JSON inválido em presets.json: {e}")
        return False
    except Exception as e:
        print(f"✗ Erro: {e}")
        return False


def test_no_sensitive_files():
    """Verifica se não há arquivos sensíveis no repositório"""
    sensitive_patterns = ['.env', 'secrets', 'credentials', '.pem', '.key']
    root_dir = os.path.join(os.path.dirname(__file__), '..')
    
    found_sensitive = []
    for root, dirs, files in os.walk(root_dir):
        # Ignora diretórios .git e __pycache__
        if '.git' in root or '__pycache__' in root or 'node_modules' in root:
            continue
            
        for file in files:
            for pattern in sensitive_patterns:
                if pattern in file.lower():
                    found_sensitive.append(os.path.join(root, file))
    
    if found_sensitive:
        print(f"✗ Erro: Arquivos sensíveis encontrados: {found_sensitive}")
        return False
    
    print("✓ Teste de arquivos sensíveis passou")
    return True


def test_scripts_syntax():
    """Verifica a sintaxe dos scripts Python"""
    scripts_dir = os.path.join(os.path.dirname(__file__), '..', 'scripts')
    
    if not os.path.exists(scripts_dir):
        print("⚠ Diretório de scripts não encontrado")
        return True
    
    errors = []
    for filename in os.listdir(scripts_dir):
        if filename.endswith('.py'):
            filepath = os.path.join(scripts_dir, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    compile(f.read(), filepath, 'exec')
                print(f"✓ Sintaxe válida: {filename}")
            except SyntaxError as e:
                errors.append(f"{filename}: {e}")
                print(f"✗ Erro de sintaxe em {filename}: {e}")
    
    if errors:
        return False
    
    print("✓ Teste de sintaxe dos scripts passou")
    return True


def test_error_log_sanitization():
    """Testa se o sistema de logs sanitiza dados sensíveis"""
    scripts_dir = os.path.join(os.path.dirname(__file__), '..', 'scripts')
    sys.path.insert(0, scripts_dir)
    
    try:
        from sanitize_logs import sanitize_error_message
        
        test_cases = [
            ("password: mypassword123", "[REDACTED"),
            ("api_key: sk-abc123xyz78901234567890", "[REDACTED"),
            ("token: ghp_abcdefghijklmnopqrstuvwxyz0123456789", "[REDACTED"),
            ("Bearer abc123token", "[REDACTED"),
        ]
        
        all_passed = True
        for input_msg, expected_pattern in test_cases:
            result = sanitize_error_message(input_msg)
            if expected_pattern == "[REDACTED" and "[REDACTED" not in result:
                print(f"✗ Falha na sanitização: '{input_msg}' -> '{result}'")
                all_passed = False
        
        if all_passed:
            print("✓ Teste de sanitização de logs passou")
        return all_passed
    
    except ImportError as e:
        print(f"⚠ Módulo sanitize_logs não encontrado: {e}")
        return True
    except Exception as e:
        print(f"✗ Erro no teste de sanitização: {e}")
        return False
    finally:
        if scripts_dir in sys.path:
            sys.path.remove(scripts_dir)


def run_all_tests():
    """Executa todos os testes"""
    print("=" * 60)
    print("EXECUTANDO PIPELINE DE TESTES")
    print("=" * 60)
    
    tests = [
        test_presets_valid,
        test_no_sensitive_files,
        test_scripts_syntax,
    ]
    
    # Adiciona teste de sanitização apenas se o módulo existir
    sanitize_path = os.path.join(os.path.dirname(__file__), '..', 'scripts', 'sanitize_logs.py')
    if os.path.exists(sanitize_path):
        tests.append(test_error_log_sanitization)
    
    results = []
    for test in tests:
        try:
            results.append(test())
        except Exception as e:
            print(f"✗ Teste {test.__name__} falhou com exceção: {e}")
            results.append(False)
    
    print("=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"RESULTADO: {passed}/{total} testes passaram")
    print("=" * 60)
    
    if all(results):
        print("✅ TODOS OS TESTES PASSARAM - Pipeline aprovado")
        return 0
    else:
        print("❌ ALGUNS TESTES FALHARAM - Pipeline reprovado")
        return 1


if __name__ == '__main__':
    sys.exit(run_all_tests())
