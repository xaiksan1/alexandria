#!/usr/bin/env python3
"""
Alexa Configuration Manager
Manages Terraform, Docker, Kubernetes, OPA, and Guacamole configurations
Bridges between Alexa UI and infrastructure provisioning tools
"""

import os
import sys
import json
import yaml
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] ALEXA_CONFIG: %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('cyber-gate.log', mode='a'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ============================================================================
# DATA MODELS
# ============================================================================

@dataclass
class TerraformConfig:
    """Terraform configuration"""
    workspace: str
    region: str
    environment: str
    variables: Dict[str, Any]

@dataclass
class DockerConfig:
    """Docker configuration"""
    registry_url: str
    registry_username: str
    build_context: str
    dockerfile_path: str
    registry_password: str = "***REDACTED***"

@dataclass
class KubernetesConfig:
    """Kubernetes configuration"""
    cluster_name: str
    cluster_endpoint: str
    namespace: str
    kubeconfig_path: str

@dataclass
class OPAConfig:
    """OPA Policy configuration"""
    policies_path: str
    enforcement_level: str  # "audit", "warn", "deny"
    policy_files: List[str]

@dataclass
class GuacamoleConfig:
    """Guacamole gateway configuration"""
    gateway_host: str
    gateway_port: int
    guacd_host: str
    guacd_port: int
    database_url: str
    enable_zangetsu: bool = True
    enable_chapel_xvi: bool = True

# ============================================================================
# ALEXA CONFIG MANAGER
# ============================================================================

class AlexaConfigManager:
    """Manages all Alexa infrastructure configurations"""

    def __init__(self, porta_mundi_path: str = "/home/ichigo/alexandria/ADAM/porta-mundi"):
        self.base_path = Path(porta_mundi_path)
        self.alexa_path = self.base_path / "Alexa"
        self.config_path = self.base_path / "config"
        self.config_path.mkdir(exist_ok=True)

        # Load configurations
        self.terraform_config = self._load_terraform_config()
        self.docker_config = self._load_docker_config()
        self.kubernetes_config = self._load_kubernetes_config()
        self.opa_config = self._load_opa_config()
        self.guacamole_config = self._load_guacamole_config()

        logger.info("Alexa Config Manager initialized")

    # ========================================================================
    # CONFIGURATION LOADING
    # ========================================================================

    def _load_terraform_config(self) -> TerraformConfig:
        """Load or create Terraform configuration"""
        config_file = self.config_path / "terraform.json"

        if config_file.exists():
            with open(config_file) as f:
                data = json.load(f)
                return TerraformConfig(**data)

        # Default configuration
        config = TerraformConfig(
            workspace="production",
            region="us-east-1",
            environment="prod",
            variables={
                "instance_type": "t3.medium",
                "instance_count": 3,
                "enable_monitoring": True,
                "enable_logging": True,
            }
        )

        self._save_config(config_file, config.__dict__)
        return config

    def _load_docker_config(self) -> DockerConfig:
        """Load or create Docker configuration"""
        config_file = self.config_path / "docker.json"

        if config_file.exists():
            with open(config_file) as f:
                data = json.load(f)
                return DockerConfig(**data)

        # Default configuration
        config = DockerConfig(
            registry_url="registry.alexandria.local",
            registry_username="alexandria-deployer",
            registry_password=os.getenv("DOCKER_REGISTRY_PASSWORD", "***REDACTED***"),
            build_context=str(self.alexa_path),
            dockerfile_path="./Dockerfile"
        )

        self._save_config(config_file, config.__dict__)
        return config

    def _load_kubernetes_config(self) -> KubernetesConfig:
        """Load or create Kubernetes configuration"""
        config_file = self.config_path / "kubernetes.json"

        if config_file.exists():
            with open(config_file) as f:
                data = json.load(f)
                return KubernetesConfig(**data)

        # Default configuration
        config = KubernetesConfig(
            cluster_name="alexandria-prod",
            cluster_endpoint="https://k8s.alexandria.local",
            namespace="default",
            kubeconfig_path=os.path.expanduser("~/.kube/config")
        )

        self._save_config(config_file, config.__dict__)
        return config

    def _load_opa_config(self) -> OPAConfig:
        """Load or create OPA Policy configuration"""
        config_file = self.config_path / "opa.json"

        if config_file.exists():
            with open(config_file) as f:
                data = json.load(f)
                return OPAConfig(**data)

        # Default configuration
        config = OPAConfig(
            policies_path=str(self.alexa_path / "opa"),
            enforcement_level="deny",
            policy_files=[
                "require-encryption.rego",
                "require-https.rego",
                "require-labels.rego",
                "require-resource-limits.rego",
                "security-hardening.rego"
            ]
        )

        self._save_config(config_file, config.__dict__)
        return config

    def _load_guacamole_config(self) -> GuacamoleConfig:
        """Load or create Guacamole configuration"""
        config_file = self.config_path / "guacamole.json"

        if config_file.exists():
            with open(config_file) as f:
                data = json.load(f)
                return GuacamoleConfig(**data)

        # Default configuration
        config = GuacamoleConfig(
            gateway_host="localhost",
            gateway_port=8822,
            guacd_host="localhost",
            guacd_port=4822,
            database_url="postgresql://guacamole:password@localhost:5432/guacamole",
            enable_zangetsu=True,
            enable_chapel_xvi=True
        )

        self._save_config(config_file, config.__dict__)
        return config

    def _save_config(self, path: Path, data: Dict[str, Any]):
        """Save configuration to file"""
        try:
            with open(path, 'w') as f:
                json.dump(data, f, indent=2)
            logger.info(f"Configuration saved: {path}")
        except Exception as e:
            logger.error(f"Error saving configuration: {e}")

    # ========================================================================
    # CONFIGURATION ACCESS
    # ========================================================================

    def get_terraform_vars(self) -> Dict[str, Any]:
        """Get Terraform variables"""
        return self.terraform_config.variables

    def set_terraform_var(self, key: str, value: Any):
        """Set a Terraform variable"""
        self.terraform_config.variables[key] = value
        self._save_config(
            self.config_path / "terraform.json",
            self.terraform_config.__dict__
        )
        logger.info(f"Terraform variable updated: {key} = {value}")

    def get_docker_registry_url(self) -> str:
        """Get Docker registry URL"""
        return self.docker_config.registry_url

    def get_kubernetes_namespace(self) -> str:
        """Get Kubernetes namespace"""
        return self.kubernetes_config.namespace

    def get_opa_policies(self) -> List[str]:
        """Get OPA policy files"""
        return self.opa_config.policy_files

    def get_guacamole_endpoint(self) -> str:
        """Get Guacamole gateway endpoint"""
        return f"{self.guacamole_config.gateway_host}:{self.guacamole_config.gateway_port}"

    # ========================================================================
    # DOCKER COMPOSE GENERATION
    # ========================================================================

    def generate_docker_compose(self) -> Dict[str, Any]:
        """Generate Docker Compose configuration for Alexa stack"""
        return {
            "version": "3.8",
            "services": {
                "alexa-api": {
                    "image": "alexandria/alexa:latest",
                    "ports": ["5000:5000"],
                    "environment": {
                        "PORTA_MUNDI_PATH": str(self.base_path),
                        "GUACAMOLE_HOST": self.guacamole_config.gateway_host,
                        "GUACAMOLE_PORT": self.guacamole_config.gateway_port,
                        "ZANGETSU_ENABLED": str(self.guacamole_config.enable_zangetsu),
                        "CHAPEL_XVI_ENABLED": str(self.guacamole_config.enable_chapel_xvi),
                    },
                    "volumes": [str(self.base_path) + ":/porta-mundi"],
                    "networks": ["alexandria"],
                    "restart": "unless-stopped"
                },
                "alexa-guacamole-bridge": {
                    "image": "alexandria/alexa-guacamole-bridge:latest",
                    "ports": [f"{self.guacamole_config.gateway_port}:8822"],
                    "environment": {
                        "GUACAMOLE_HOST": self.guacamole_config.guacd_host,
                        "GUACAMOLE_PORT": self.guacamole_config.guacd_port,
                        "BRIDGE_PORT": "8822",
                    },
                    "depends_on": ["alexa-api"],
                    "networks": ["alexandria"],
                    "restart": "unless-stopped"
                }
            },
            "networks": {
                "alexandria": {
                    "driver": "bridge"
                }
            }
        }

    # ========================================================================
    # KUBERNETES MANIFESTS GENERATION
    # ========================================================================

    def generate_kubernetes_manifests(self) -> Dict[str, Any]:
        """Generate Kubernetes manifests for Alexa deployment"""
        return {
            "apiVersion": "v1",
            "kind": "Namespace",
            "metadata": {
                "name": self.kubernetes_config.namespace,
                "labels": {
                    "name": "alexandria",
                    "component": "alexa"
                }
            }
        }

    # ========================================================================
    # OPA POLICY GENERATION
    # ========================================================================

    def generate_opa_policies(self) -> Dict[str, str]:
        """Generate OPA policy files"""
        policies = {
            "require-encryption.rego": """
package main

deny[msg] {
    input.storage.encryption != "enabled"
    msg := "Storage encryption is required"
}

deny[msg] {
    input.database.encryption != "enabled"
    msg := "Database encryption is required"
}
""",
            "require-https.rego": """
package main

deny[msg] {
    input.protocol != "https"
    msg := "HTTPS is required for all connections"
}
""",
            "require-labels.rego": """
package main

deny[msg] {
    not input.metadata.labels.environment
    msg := "environment label is required"
}

deny[msg] {
    not input.metadata.labels.owner
    msg := "owner label is required"
}
""",
            "require-resource-limits.rego": """
package main

deny[msg] {
    not input.spec.containers[_].resources.limits
    msg := "Resource limits are required for all containers"
}

deny[msg] {
    not input.spec.containers[_].resources.requests
    msg := "Resource requests are required for all containers"
}
""",
            "security-hardening.rego": """
package main

deny[msg] {
    input.spec.containers[_].securityContext.privileged == true
    msg := "Privileged containers are not allowed"
}

deny[msg] {
    input.spec.containers[_].securityContext.runAsRoot == true
    msg := "Running as root is not allowed"
}
"""
        }

        return policies

    # ========================================================================
    # TERRAFORM GENERATION
    # ========================================================================

    def generate_terraform_config(self) -> str:
        """Generate Terraform configuration"""
        return f"""
# Alexa Infrastructure Configuration
# Generated by Alexa Config Manager

terraform {{
  required_version = ">= 1.0"

  required_providers {{
    aws = {{
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }}
  }}

  backend "s3" {{
    bucket         = "alexandria-terraform-state"
    key            = "alexa/terraform.tfstate"
    region         = "{self.terraform_config.region}"
    encrypt        = true
    dynamodb_table = "terraform-lock"
  }}
}}

provider "aws" {{
  region = "{self.terraform_config.region}"

  default_tags {{
    tags = {{
      Environment = "{self.terraform_config.environment}"
      Component   = "alexa"
      ManagedBy   = "terraform"
      CreatedBy   = "alexandria"
    }}
  }}
}}

# Variables from config
variable "instance_type" {{
  default = "{self.terraform_config.variables.get('instance_type', 't3.medium')}"
}}

variable "instance_count" {{
  default = {self.terraform_config.variables.get('instance_count', 3)}
}}

variable "enable_monitoring" {{
  default = {str(self.terraform_config.variables.get('enable_monitoring', True)).lower()}
}}
"""

    # ========================================================================
    # CONFIGURATION SUMMARY
    # ========================================================================

    def get_summary(self) -> Dict[str, Any]:
        """Get configuration summary"""
        return {
            "terraform": {
                "workspace": self.terraform_config.workspace,
                "region": self.terraform_config.region,
                "environment": self.terraform_config.environment,
                "variables": self.terraform_config.variables,
            },
            "docker": {
                "registry": self.docker_config.registry_url,
                "build_context": self.docker_config.build_context,
            },
            "kubernetes": {
                "cluster": self.kubernetes_config.cluster_name,
                "namespace": self.kubernetes_config.namespace,
            },
            "opa": {
                "enforcement_level": self.opa_config.enforcement_level,
                "policy_count": len(self.opa_config.policy_files),
            },
            "guacamole": {
                "gateway": self.get_guacamole_endpoint(),
                "zangetsu_enabled": self.guacamole_config.enable_zangetsu,
                "chapel_xvi_enabled": self.guacamole_config.enable_chapel_xvi,
            }
        }

# ============================================================================
# CLI INTERFACE
# ============================================================================

def main():
    """Configuration manager CLI"""
    import argparse

    parser = argparse.ArgumentParser(description="Alexa Configuration Manager")
    parser.add_argument("command", choices=["summary", "terraform", "docker", "kubernetes", "opa", "generate-compose"])
    args = parser.parse_args()

    manager = AlexaConfigManager()

    if args.command == "summary":
        print(json.dumps(manager.get_summary(), indent=2))

    elif args.command == "terraform":
        print(manager.generate_terraform_config())

    elif args.command == "docker":
        print(json.dumps(manager.generate_docker_compose(), indent=2))

    elif args.command == "kubernetes":
        print(json.dumps(manager.generate_kubernetes_manifests(), indent=2))

    elif args.command == "opa":
        policies = manager.generate_opa_policies()
        for filename, content in policies.items():
            print(f"\n=== {filename} ===\n{content}")

    elif args.command == "generate-compose":
        compose = manager.generate_docker_compose()
        with open(manager.base_path / "docker-compose-alexa.yml", 'w') as f:
            yaml.dump(compose, f, default_flow_style=False)
        print(f"Docker Compose file generated: docker-compose-alexa.yml")

if __name__ == "__main__":
    main()
