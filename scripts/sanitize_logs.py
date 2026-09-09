"""
Sistema de sanitização de logs para proteger dados sensíveis
"""
import re
import os
from datetime import datetime


def sanitize_error_message(error_message):
    if not error_message:
        return "[ERRO VAZIO]"
    
    sanitized = str(error_message)
    
    # Senhas e tokens
    sanitized = re.sub(r'password[=:]\s*\S+', '[REDACTED_PASSWORD]', sanitized, flags=re.IGNORECASE)
    sanitized = re.sub(r'passwd[=:]\s*\S+', '[REDACTED_PASSWORD]', sanitized, flags=re.IGNORECASE)
    sanitized = re.sub(r'secret[=:]\s*\S+', '[REDACTED_SECRET]', sanitized, flags=re.IGNORECASE)
    sanitized = re.sub(r'api[_-]?key[=:]\s*\S+', '[REDACTED_API_KEY]', sanitized, flags=re.IGNORECASE)
    sanitized = re.sub(r'token[=:]\s*\S+', '[REDACTED_TOKEN]', sanitized, flags=re.IGNORECASE)
    sanitized = re.sub(r'bearer\s+\S+', '[REDACTED_BEARER]', sanitized, flags=re.IGNORECASE)
    
    # Chaves específicas
    sanitized = re.sub(r'sk-[a-zA-Z0-9]{20,}', '[REDACTED_API_KEY]', sanitized)
    sanitized = re.sub(r'ghp_[a-zA-Z0-9]{36}', '[REDACTED_GITHUB_TOKEN]', sanitized)
    sanitized = re.sub(r'glpat-[a-zA-Z0-9\-]{20,}', '[REDACTED_GITLAB_TOKEN]', sanitized)
    sanitized = re.sub(r'xox[baprs]-[a-zA-Z0-9\-]{10,}', '[REDACTED_SLACK_TOKEN]', sanitized)
    
    # Informações pessoais
    sanitized = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[REDACTED_EMAIL]', sanitized)
    sanitized = re.sub(r'\b\d{3}\.?\d{3}\.?\d{3}-\d{2}\b', '[REDACTED_CPF]', sanitized)
    sanitized = re.sub(r'\b\d{2}\.?\d{3}\.?\d{3}/\d{4}-\d{2}\b', '[REDACTED_CNPJ]', sanitized)
    
    # Caminhos de arquivos sensíveis
    sanitized = re.sub(r'/home/[^/]+/', '/home/[USER]/', sanitized)
    sanitized = re.sub(r'.ssh/id_.+', '[SSH_REDACTED]', sanitized)
    sanitized = re.sub(r'\.aws/credentials', '[REDACTED_AWS_CREDENTIALS]', sanitized)
    sanitized = re.sub(r'\.env', '[REDACTED_ENV_FILE]', sanitized)
    
    # IPs e URLs com credenciais
    sanitized = re.sub(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', '[REDACTED_IP]', sanitized)
    sanitized = re.sub(r'https?://[^:]+:[^@]+@', 'https://[REDACTED_CRED]@', sanitized)
    
    return sanitized


class ErrorCollector:
    def __init__(self, log_dir='logs'):
        self.log_dir = log_dir
        self.error_file = os.path.join(log_dir, 'error_log.txt')
        self._ensure_log_dir()
    
    def _ensure_log_dir(self):
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir, exist_ok=True)
            gitignore_path = os.path.join(self.log_dir, '.gitignore')
            if not os.path.exists(gitignore_path):
                with open(gitignore_path, 'w') as f:
                    f.write("# Logs de erro contem dados sensiveis\n")
                    f.write("*.log\n")
                    f.write("*.txt\n")
                    f.write("!README.md\n")
    
    def log_error(self, error, context=""):
        timestamp = datetime.now().isoformat()
        error_id = "ERR-" + timestamp.replace(':', '-').replace('.', '-')
        
        error_msg = sanitize_error_message(str(error))
        error_type = sanitize_error_message(type(error).__name__)
        context_safe = sanitize_error_message(context) if context else ""
        
        log_entry = "\n" + "="*60 + "\n"
        log_entry += "ERROR ID: " + error_id + "\n"
        log_entry += "TIMESTAMP: " + timestamp + "\n"
        log_entry += "TYPE: " + error_type + "\n"
        log_entry += "CONTEXT: " + context_safe + "\n"
        log_entry += "MESSAGE: " + error_msg + "\n"
        log_entry += "="*60 + "\n"
        
        try:
            with open(self.error_file, 'a', encoding='utf-8') as f:
                f.write(log_entry)
        except Exception as write_error:
            return "ERR-WRITE-FAILED: " + sanitize_error_message(str(write_error))
        
        return error_id
    
    def get_recent_errors(self, limit=10):
        if not os.path.exists(self.error_file):
            return []
        
        errors = []
        try:
            with open(self.error_file, 'r', encoding='utf-8') as f:
                content = f.read()
                raw_errors = content.split('=' * 60)
                errors = [e.strip() for e in raw_errors[-limit:] if e.strip()]
        except Exception:
            pass
        
        return errors


error_collector = ErrorCollector()


def safe_execute(func, *args, **kwargs):
    context = kwargs.pop('context', '')
    try:
        result = func(*args, **kwargs)
        return True, result
    except Exception as e:
        error_id = error_collector.log_error(e, context)
        return False, "Erro registrado: " + error_id
