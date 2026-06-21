import os
import re


def validate_frontend(module_path, module_name):
    print(f"
🔍 Analizando módulo: {module_name}...")
    errors = []
    
    # 1. Verificar estructura de archivos
    required_files = {
        'index.html': module_path + '/index.html',
        'config.js': module_path + '/js/config.js',
        'api.js': module_path + '/js/api.js',
        'app.js': module_path + '/js/app.js',
        'style.css': module_path + '/css/style.css'
    }
    
    for name, path in required_files.items():
        if not os.path.exists(path):
            errors.append(f"❌ Archivo faltante: {name}")

    # 2. Verificar orden de carga en index.html
    if os.path.exists(required_files['index.html']):
        with open(required_files['index.html'], 'r', encoding='utf-8') as f:
            content = f.read()
            # Verificar orden de scripts
            pos_config = content.find('src="js/config.js"')
            pos_api = content.find('src="js/api.js"')
            pos_app = content.find('src="js/app.js"')
            
            if pos_config == -1 or pos_api == -1 or pos_app == -1:
                errors.append("❌ Scripts no referenciados correctamente en index.html")
            elif not (pos_config < pos_api < pos_app):
                errors.append("❌ Orden de carga incorrecto (debe ser: config -> api -> app)")

    # 3. Verificar Modo Mock en config.js
    if os.path.exists(required_files['config.js']):
        with open(required_files['config.js'], 'r', encoding='utf-8') as f:
            content = f.read()
            if 'IS_MOCK_MODE: true' not in content:
                errors.append("⚠️ IS_MOCK_MODE no está activo o no existe en config.js")

    # 4. Análisis básico de sintaxis JS (balance de llaves)
    for js_file in ['config.js', 'api.js', 'app.js']:
        path = module_path + '/js/' + js_file
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
                if content.count('{') != content.count('}'):
                    errors.append(f"❌ Error de sintaxis en {js_file}: Llaves {{ }} no balanceadas")
                if content.count('(') != content.count(')'):
                    errors.append(f"❌ Error de sintaxis en {js_file}: Paréntesis ( ) no balanceados")

    if not errors:
        print(f"✅ {module_name}: TODO CORRECTO. Listo para testeo offline.")
        return True
    else:
        for err in errors:
            print(err)
        return False

if __name__ == "__main__":
    base_path = "/home/adrian/Escritorio/Nueva carpeta 2/frontends_offline_global"
    modules = ["mercado-pago", "whatsapp", "stock"]
    
    print("🚀 Iniciando Validación Pre-commit de Frontends...")
    print("===================================================")
    
    all_passed = True
    for mod in modules:
        if not validate_frontend(base_path + "/" + mod, mod):
            all_passed = False
            
    print("===================================================")
    if all_passed:
        print("
🎉 RESULTADO FINAL: Todos los módulos pasan la validación. ¡Puedes testear offline!")
    else:
        print("
🛑 RESULTADO FINAL: Se encontraron errores. Revisa los logs arriba.")
