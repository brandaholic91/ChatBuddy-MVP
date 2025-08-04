#!/usr/bin/env python3
"""
Supabase kapcsolat tesztelő szkript
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Hozzáadjuk a projekt gyökérkönyvtárát a Python path-hoz
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Betöltjük a .env fájlt
load_dotenv()

def test_supabase_connection():
    """Teszteli a Supabase kapcsolatot"""
    
    print("🔍 Supabase kapcsolat tesztelése...")
    print("=" * 50)
    
    # Ellenőrizzük a környezeti változókat
    required_vars = [
        "SUPABASE_URL",
        "SUPABASE_ANON_KEY", 
        "SUPABASE_SERVICE_KEY"
    ]
    
    missing_vars = []
    for var in required_vars:
        value = os.getenv(var)
        if not value:
            missing_vars.append(var)
        else:
            # Csak az első 10 karaktert mutatjuk a biztonság érdekében
            masked_value = value[:10] + "..." if len(value) > 10 else value
            print(f"✅ {var}: {masked_value}")
    
    if missing_vars:
        print(f"\n❌ Hiányzó környezeti változók: {', '.join(missing_vars)}")
        print("Kérlek töltsd ki a .env fájlt a hiányzó változókkal!")
        return False
    
    print("\n🔗 Kapcsolat tesztelése...")
    
    try:
        # Importáljuk a Supabase klienst
        from src.integrations.database.supabase_client import SupabaseClient
        
        # Létrehozzuk a klienst
        client = SupabaseClient()
        
        # Teszteljük a kapcsolatot
        if client.test_connection():
            print("✅ Supabase kapcsolat sikeres!")
            
            # Teszteljük a service role klienst is
            try:
                service_client = client.get_service_client()
                print("✅ Service role kliens is működik!")
            except Exception as e:
                print(f"⚠️ Service role kliens hiba: {e}")
            
            return True
        else:
            print("❌ Supabase kapcsolat sikertelen!")
            return False
            
    except ImportError as e:
        print(f"❌ Import hiba: {e}")
        print("Kérlek telepítsd a szükséges csomagokat: pip install -r requirements.txt")
        return False
    except Exception as e:
        print(f"❌ Kapcsolat hiba: {e}")
        return False

def test_environment_variables():
    """Teszteli a környezeti változókat"""
    
    print("🔧 Környezeti változók tesztelése...")
    print("=" * 50)
    
    # Ellenőrizzük a biztonsági változókat
    security_vars = [
        ("SECRET_KEY", 32),
        ("JWT_SECRET", 32)
    ]
    
    for var, min_length in security_vars:
        value = os.getenv(var)
        if not value:
            print(f"❌ {var}: Hiányzó")
        elif len(value) < min_length:
            print(f"⚠️ {var}: Túl rövid (minimum {min_length} karakter)")
        else:
            masked_value = value[:10] + "..."
            print(f"✅ {var}: {masked_value}")
    
    # Ellenőrizzük az AI API kulcsokat
    ai_vars = [
        ("OPENAI_API_KEY", 20),
        ("ANTHROPIC_API_KEY", 20)
    ]
    
    for var, min_length in ai_vars:
        value = os.getenv(var)
        if not value:
            print(f"⚠️ {var}: Hiányzó (opcionális)")
        elif len(value) < min_length:
            print(f"⚠️ {var}: Túl rövid (minimum {min_length} karakter)")
        else:
            masked_value = value[:10] + "..."
            print(f"✅ {var}: {masked_value}")

if __name__ == "__main__":
    print("🚀 Chatbuddy MVP - Supabase Kapcsolat Teszt")
    print("=" * 60)
    
    # Teszteljük a környezeti változókat
    test_environment_variables()
    print()
    
    # Teszteljük a kapcsolatot
    success = test_supabase_connection()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 Minden rendben! A Supabase kapcsolat működik.")
    else:
        print("💥 Problémák vannak a kapcsolattal. Kérlek ellenőrizd a konfigurációt.")
    
    sys.exit(0 if success else 1) 