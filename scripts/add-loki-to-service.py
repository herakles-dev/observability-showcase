#!/usr/bin/env python3
"""
Automatically add Loki logging to docker-compose.yml files
"""
import yaml
import sys
from pathlib import Path

LOKI_CONFIG_TEMPLATE = {
    'driver': 'loki',
    'options': {
        'loki-url': 'http://localhost:3100/loki/api/v1/push',
        'loki-batch-size': '400',
        'loki-retries': '5',
    }
}

def add_loki_to_compose(file_path, service_mappings):
    """
    Add Loki logging to specified services in docker-compose.yml
    
    Args:
        file_path: Path to docker-compose.yml
        service_mappings: Dict of {service_name: {'environment': 'prod', 'type': 'api'}}
    """
    with open(file_path, 'r') as f:
        content = f.read()
    
    data = yaml.safe_load(content)
    
    if 'services' not in data:
        print(f"❌ No services found in {file_path}")
        return False
    
    modified = False
    for service_name, labels in service_mappings.items():
        if service_name not in data['services']:
            print(f"⚠️  Service '{service_name}' not found in compose file")
            continue
        
        service = data['services'][service_name]
        
        if 'logging' in service:
            print(f"⚠️  Service '{service_name}' already has logging configured")
            continue
        
        loki_labels = f"service={labels.get('service', service_name)},environment={labels['environment']},type={labels['type']}"
        
        logging_config = LOKI_CONFIG_TEMPLATE.copy()
        logging_config['options']['loki-external-labels'] = loki_labels
        
        service['logging'] = logging_config
        modified = True
        print(f"✅ Added Loki logging to '{service_name}' ({labels['type']})")
    
    if modified:
        with open(file_path, 'w') as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False, width=1000)
        print(f"💾 Saved changes to {file_path}")
        return True
    
    return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 add-loki-to-service.py <compose-file> [service:env:type] ...")
        print("Example: python3 add-loki-to-service.py docker-compose.yml backend:production:api postgres:production:database")
        sys.exit(1)
    
    compose_file = sys.argv[1]
    
    if not Path(compose_file).exists():
        print(f"❌ File not found: {compose_file}")
        sys.exit(1)
    
    service_mappings = {}
    for arg in sys.argv[2:]:
        parts = arg.split(':')
        if len(parts) != 3:
            print(f"⚠️  Invalid format: {arg} (expected service:environment:type)")
            continue
        
        service, env, svc_type = parts
        service_mappings[service] = {
            'service': service,
            'environment': env,
            'type': svc_type
        }
    
    if service_mappings:
        success = add_loki_to_compose(compose_file, service_mappings)
        sys.exit(0 if success else 1)
    else:
        print("❌ No valid service mappings provided")
        sys.exit(1)
