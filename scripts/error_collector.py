#!/usr/bin/env python3
"""
Sistema de Coleta e Registro de Erros para Qwen Inference
Salva erros em arquivo seguro, sem expor informações sensíveis
"""

import os
import sys
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
import hashlib
import platform

class ErrorCollector:
    """Coletor de erros que sanitiza informações sensíveis antes de salvar"""
    
    def __init__(self, log_dir: str = "logs", max_log_size_mb: int = 10):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.error_file = self.log_dir / "errors.jsonl"
        self.max_log_size_mb = max_log_size_mb
        self.sensitive_patterns = [
            'password', 'token', 'key', 'secret', 'api_key', 
            'authorization', 'credential', 'private'
        ]
        
        # Configurar logger
        self.logger = logging.getLogger("ErrorCollector")
        self.logger.setLevel(logging.ERROR)
        
    def _sanitize_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Remove ou ofusca informações sensíveis dos dados"""
        sanitized = {}
        for key, value in data.items():
            key_lower = key.lower()
            
            # Verificar se a chave contém padrões sensíveis
            if any(pattern in key_lower for pattern in self.sensitive_patterns):
                sanitized[key] = "***REDACTED***"
            elif isinstance(value, dict):
                sanitized[key] = self._sanitize_data(value)
            elif isinstance(value, str):
                # Verificar se o valor contém padrões sensíveis
                if any(pattern in value.lower() for pattern in self.sensitive_patterns):
                    sanitized[key] = "***REDACTED***"
                else:
                    sanitized[key] = value
            else:
                sanitized[key] = value
                
        return sanitized
    
    def _rotate_log_if_needed(self):
        """Rotaciona o arquivo de log se exceder o tamanho máximo"""
        if self.error_file.exists():
            size_mb = self.error_file.stat().st_size / (1024 * 1024)
            if size_mb > self.max_log_size_mb:
                # Renomear arquivo antigo com timestamp
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                old_file = self.log_dir / f"errors_{timestamp}.jsonl"
                self.error_file.rename(old_file)
                
    def collect_error(
        self,
        error: Exception,
        context: Optional[Dict[str, Any]] = None,
        severity: str = "ERROR"
    ) -> str:
        """
        Coleta um erro, sanitiza os dados e salva no arquivo
        
        Returns:
            str: ID do erro gerado
        """
        self._rotate_log_if_needed()
        
        # Obter informações do sistema (sem dados sensíveis)
        system_info = {
            "os": platform.system(),
            "os_version": platform.version(),
            "python_version": sys.version.split()[0],
            "architecture": platform.machine(),
            "processor": platform.processor() or "unknown"
        }
        
        # Criar registro de erro
        error_record = {
            "timestamp": datetime.utcnow().isoformat(),
            "error_id": hashlib.md5(
                f"{datetime.utcnow().isoformat()}{str(error)}".encode()
            ).hexdigest()[:12],
            "severity": severity,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "system_info": system_info,
            "context": self._sanitize_data(context or {}),
            "traceback_lines": []
        }
        
        # Extrair traceback sem informações de caminho completo
        import traceback
        tb_lines = traceback.format_exception(type(error), error, error.__traceback__)
        for line in tb_lines:
            # Sanitizar caminhos de arquivo
            sanitized_line = line.replace(str(Path.home()), "~")
            if "/workspace/" in sanitized_line:
                sanitized_line = sanitized_line.split("/workspace/")[-1]
            error_record["traceback_lines"].append(sanitized_line.strip())
        
        # Salvar erro no arquivo
        with open(self.error_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(error_record, ensure_ascii=False) + "\n")
        
        return error_record["error_id"]
    
    def get_recent_errors(self, limit: int = 10) -> list:
        """Retorna os últimos erros registrados"""
        if not self.error_file.exists():
            return []
            
        errors = []
        with open(self.error_file, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    errors.append(json.loads(line.strip()))
                except json.JSONDecodeError:
                    continue
                    
        return errors[-limit:]
    
    def clear_errors(self):
        """Limpa todos os erros registrados"""
        if self.error_file.exists():
            self.error_file.unlink()


# Singleton instance
_error_collector: Optional[ErrorCollector] = None

def get_error_collector() -> ErrorCollector:
    """Obtém a instância singleton do coletor de erros"""
    global _error_collector
    if _error_collector is None:
        _error_collector = ErrorCollector()
    return _error_collector


def setup_error_handling():
    """Configura tratamento global de erros"""
    collector = get_error_collector()
    
    def handle_exception(exc_type, exc_value, exc_traceback):
        """Handler global para exceções não tratadas"""
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
            
        error = exc_value
        context = {
            "module": "__main__",
            "unhandled": True
        }
        error_id = collector.collect_error(error, context, severity="CRITICAL")
        print(f"\n❌ Erro crítico detectado. ID: {error_id}")
        print(f"Detalhes salvos em: {collector.error_file}")
    
    sys.excepthook = handle_exception
    return collector


if __name__ == "__main__":
    # Teste do coletor de erros
    print("Testando ErrorCollector...")
    collector = setup_error_handling()
    
    try:
        raise ValueError("Erro de teste com senha=12345")
    except Exception as e:
        error_id = collector.collect_error(
            e,
            context={"user_input": "teste", "api_key": "secret123"},
            severity="WARNING"
        )
        print(f"Erro coletado com ID: {error_id}")
    
    recent = collector.get_recent_errors(limit=5)
    print(f"\nÚltimos erros: {len(recent)}")
    for err in recent:
        print(f"  - [{err['severity']}] {err['error_type']}: {err['error_message']}")
        print(f"    Contexto sanitizado: {err['context']}")
    
    print("\n✅ Teste concluído!")
