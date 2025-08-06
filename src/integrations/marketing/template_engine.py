"""
Jinja2 template engine a marketing automation-hoz
"""
from jinja2 import Environment, FileSystemLoader, Template, select_autoescape
import os
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)

class MarketingTemplateEngine:
    """
    Jinja2 alapú template engine a marketing automation-hoz
    """
    
    def __init__(self):
        """Template engine inicializálása"""
        # Template könyvtárak beállítása
        template_dirs = [
            'templates/marketing',
            'src/integrations/marketing/templates',
            os.path.join(os.path.dirname(__file__), 'templates')
        ]
        
        # Létező template könyvtárak keresése
        existing_dirs = [d for d in template_dirs if os.path.exists(d)]
        
        if not existing_dirs:
            # Ha nincs template könyvtár, létrehozzuk az alapértelmezettet
            default_dir = os.path.join(os.path.dirname(__file__), 'templates')
            os.makedirs(default_dir, exist_ok=True)
            self._create_default_templates(default_dir)
            existing_dirs = [default_dir]
        
        # Jinja2 environment létrehozása
        self.env = Environment(
            loader=FileSystemLoader(existing_dirs),
            autoescape=select_autoescape(['html', 'xml']),
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        # Custom filters hozzáadása
        self._add_custom_filters()
        
        logger.info(f"Marketing template engine inicializálva: {existing_dirs}")
    
    def render_email_template(self, template_name: str, data: Dict[str, Any]) -> str:
        """
        Email template renderelés
        
        Args:
            template_name: Template neve (pl. 'abandoned_cart')
            data: Template adatok
            
        Returns:
            str: Renderelt HTML tartalom
        """
        try:
            # Template fájl neve
            template_file = f"{template_name}.html"
            
            # Template betöltése
            template = self.env.get_template(template_file)
            
            # Adatok előkészítése
            template_data = self._prepare_template_data(data)
            
            # Template renderelés
            rendered_content = template.render(**template_data)
            
            logger.debug(f"Email template renderelés sikeres: {template_name}")
            return rendered_content
            
        except Exception as e:
            logger.error(f"Hiba az email template renderelésben: {template_name}, hiba: {e}")
            # Fallback template
            return self._get_fallback_email_template(template_name, data)
    
    def render_text_template(self, template_name: str, data: Dict[str, Any]) -> str:
        """
        Text template renderelés (plain text email-ekhez)
        
        Args:
            template_name: Template neve
            data: Template adatok
            
        Returns:
            str: Renderelt text tartalom
        """
        try:
            # Template fájl neve
            template_file = f"{template_name}.txt"
            
            # Template betöltése
            template = self.env.get_template(template_file)
            
            # Adatok előkészítése
            template_data = self._prepare_template_data(data)
            
            # Template renderelés
            rendered_content = template.render(**template_data)
            
            logger.debug(f"Text template renderelés sikeres: {template_name}")
            return rendered_content
            
        except Exception as e:
            logger.error(f"Hiba a text template renderelésben: {template_name}, hiba: {e}")
            # Fallback template
            return self._get_fallback_text_template(template_name, data)
    
    def render_sms_template(self, template_name: str, data: Dict[str, Any]) -> str:
        """
        SMS template renderelés
        
        Args:
            template_name: Template neve
            data: Template adatok
            
        Returns:
            str: Renderelt SMS tartalom
        """
        try:
            # Template fájl neve
            template_file = f"{template_name}.txt"
            
            # Template betöltése
            template = self.env.get_template(template_file)
            
            # Adatok előkészítése
            template_data = self._prepare_template_data(data)
            
            # Template renderelés
            rendered_content = template.render(**template_data)
            
            logger.debug(f"SMS template renderelés sikeres: {template_name}")
            return rendered_content
            
        except Exception as e:
            logger.error(f"Hiba az SMS template renderelésben: {template_name}, hiba: {e}")
            # Fallback template
            return self._get_fallback_sms_template(template_name, data)
    
    def _prepare_template_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Template adatok előkészítése
        
        Args:
            data: Nyers template adatok
            
        Returns:
            Dict: Előkészített template adatok
        """
        template_data = data.copy()
        
        # Alapértelmezett értékek hozzáadása
        template_data.update({
            'current_date': datetime.now().strftime('%Y-%m-%d'),
            'current_time': datetime.now().strftime('%H:%M'),
            'year': datetime.now().year,
            'company_name': os.getenv('COMPANY_NAME', 'ChatBuddy'),
            'website_url': os.getenv('WEBSITE_URL', 'https://chatbuddy.com'),
            'support_email': os.getenv('SUPPORT_EMAIL', 'support@chatbuddy.com'),
            'support_phone': os.getenv('SUPPORT_PHONE', '+36 1 234 5678'),
                    'discount_percentage': template_data.get('discount_percentage', 15.0),
        'discount_code': template_data.get('discount_code', ''),
        'cart_total': template_data.get('cart_total', 0.0),
        'customer_name': template_data.get('customer_name', 'Kedves Vásárló'),
        'valid_until': template_data.get('valid_until', (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d'))
        })
        
        # Cart items formázása
        if 'cart_items' in template_data:
            template_data['cart_items'] = self._format_cart_items(template_data['cart_items'])
        
        # Árak formázása
        if 'cart_value' in template_data:
            template_data['formatted_cart_value'] = self._format_price(template_data['cart_value'])
        
        if 'discount_amount' in template_data:
            template_data['formatted_discount_amount'] = self._format_price(template_data['discount_amount'])
        
        return template_data
    
    def _format_cart_items(self, cart_items: list) -> list:
        """
        Kosár tételek formázása
        
        Args:
            cart_items: Kosár tételek listája
            
        Returns:
            list: Formázott kosár tételek
        """
        formatted_items = []
        
        for item in cart_items:
            formatted_item = item.copy()
            
            # Ár formázása
            if 'price' in item:
                formatted_item['formatted_price'] = self._format_price(item['price'])
            
            if 'total_price' in item:
                formatted_item['formatted_total_price'] = self._format_price(item['total_price'])
            
            formatted_items.append(formatted_item)
        
        return formatted_items
    
    def _format_price(self, price: float) -> str:
        """
        Ár formázása magyar formátumra
        
        Args:
            price: Ár számként
            
        Returns:
            str: Formázott ár
        """
        try:
            return f"{price:,.0f} Ft"
        except (ValueError, TypeError):
            return str(price)
    
    def _add_custom_filters(self):
        """
        Custom Jinja2 filterek hozzáadása
        """
        # Ár formázó filter
        def format_price(value):
            return self._format_price(value)
        
        # Dátum formázó filter
        def format_date(value, format_str='%Y-%m-%d'):
            if isinstance(value, str):
                try:
                    value = datetime.fromisoformat(value.replace('Z', '+00:00'))
                except ValueError:
                    return value
            return value.strftime(format_str)
        
        # Százalék formázó filter
        def format_percentage(value):
            try:
                return f"{float(value):.1f}%"
            except (ValueError, TypeError):
                return str(value)
        
        # Filterek regisztrálása
        self.env.filters['format_price'] = format_price
        self.env.filters['format_date'] = format_date
        self.env.filters['format_percentage'] = format_percentage
    
    def _create_default_templates(self, template_dir: str):
        """
        Alapértelmezett template-ek létrehozása
        
        Args:
            template_dir: Template könyvtár útvonala
        """
        # Email template-ek
        email_templates = {
            'abandoned_cart.html': self._get_default_abandoned_cart_email_template(),
            'welcome.html': self._get_default_welcome_email_template(),
            'discount_reminder.html': self._get_default_discount_reminder_email_template()
        }
        
        # Text template-ek
        text_templates = {
            'abandoned_cart.txt': self._get_default_abandoned_cart_text_template(),
            'welcome.txt': self._get_default_welcome_text_template(),
            'discount_reminder.txt': self._get_default_discount_reminder_text_template()
        }
        
        # Template-ek létrehozása
        for filename, content in {**email_templates, **text_templates}.items():
            filepath = os.path.join(template_dir, filename)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
        
        logger.info(f"Alapértelmezett template-ek létrehozva: {template_dir}")
    
    def _get_default_abandoned_cart_email_template(self) -> str:
        """Alapértelmezett abandoned cart email template"""
        return """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Ne felejtsd el a kosaradat!</title>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: #007bff; color: white; padding: 20px; text-align: center; }
        .content { padding: 20px; background: #f8f9fa; }
        .cart-items { margin: 20px 0; }
        .cart-item { background: white; padding: 10px; margin: 10px 0; border-left: 4px solid #007bff; }
        .discount-box { background: #28a745; color: white; padding: 15px; margin: 20px 0; text-align: center; }
        .button { display: inline-block; background: #007bff; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; }
        .footer { text-align: center; padding: 20px; color: #666; font-size: 12px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🛒 Ne felejtsd el a kosaradat!</h1>
        </div>
        
        <div class="content">
            <p>Kedves {{ customer_name or 'Vásárló' }}!</p>
            
            <p>Észrevettük, hogy a kosaradban {{ cart_items|length }} termék vár a megvásárlásra, 
            összesen <strong>{{ formatted_cart_value }}</strong> értékben.</p>
            
            {% if cart_items %}
            <div class="cart-items">
                <h3>A kosaradban lévő termékek:</h3>
                {% for item in cart_items %}
                <div class="cart-item">
                    <strong>{{ item.name }}</strong><br>
                    Mennyiség: {{ item.quantity }} db<br>
                    Ár: {{ item.formatted_price }} / db<br>
                    Összesen: {{ item.formatted_total_price }}
                </div>
                {% endfor %}
            </div>
            {% endif %}
            
            {% if discount_code %}
            <div class="discount-box">
                <h3>🎁 Különleges kedvezmény!</h3>
                <p>Használd a <strong>{{ discount_code }}</strong> kódot és spórolj {{ discount_percentage|format_percentage }}-ot!</p>
                <p><small>Kedvezmény érvényes: {{ valid_until|format_date('%Y.%m.%d') }}-ig</small></p>
            </div>
            {% endif %}
            
            <p style="text-align: center; margin: 30px 0;">
                <a href="{{ website_url }}/cart" class="button">Vissza a kosarhoz</a>
            </p>
            
            <p>Ha kérdésed van, ne habozz kapcsolatba lépni velünk!</p>
        </div>
        
        <div class="footer">
            <p>{{ company_name }} | {{ website_url }}</p>
            <p>Email: {{ support_email }} | Tel: {{ support_phone }}</p>
            <p><a href="{{ website_url }}/unsubscribe">Leiratkozás</a></p>
        </div>
    </div>
</body>
</html>"""
    
    def _get_default_welcome_email_template(self) -> str:
        """Alapértelmezett welcome email template"""
        return """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Üdvözöljük a ChatBuddy-ban!</title>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: #28a745; color: white; padding: 20px; text-align: center; }
        .content { padding: 20px; background: #f8f9fa; }
        .welcome-box { background: #d4edda; border: 1px solid #c3e6cb; padding: 15px; margin: 20px 0; }
        .button { display: inline-block; background: #28a745; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; }
        .footer { text-align: center; padding: 20px; color: #666; font-size: 12px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎉 Üdvözöljük a ChatBuddy-ban!</h1>
        </div>
        
        <div class="content">
            <p>Kedves {{ customer_name or 'Vásárló' }}!</p>
            
            <div class="welcome-box">
                <h3>Köszönjük, hogy csatlakozott hozzánk!</h3>
                <p>Most már részese a ChatBuddy közösségének, ahol:</p>
                <ul>
                    <li>Gyors és szakmailag felkészült AI asszisztens segít a vásárlásban</li>
                    <li>Különleges kedvezményeket és ajánlatokat kap</li>
                    <li>Először értesül új termékekről és kampányokról</li>
                </ul>
            </div>
            
            {% if welcome_discount %}
            <div style="background: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; margin: 20px 0;">
                <h3>🎁 Üdvözlő ajánlat!</h3>
                <p>Használd a <strong>{{ welcome_discount }}</strong> kódot és spórolj {{ discount_percentage|format_percentage }}-ot az első rendelésedben!</p>
            </div>
            {% endif %}
            
            <p style="text-align: center; margin: 30px 0;">
                <a href="{{ website_url }}" class="button">Böngészés kezdése</a>
            </p>
        </div>
        
        <div class="footer">
            <p>{{ company_name }} | {{ website_url }}</p>
            <p>Email: {{ support_email }} | Tel: {{ support_phone }}</p>
            <p><a href="{{ website_url }}/unsubscribe">Leiratkozás</a></p>
        </div>
    </div>
</body>
</html>"""
    
    def _get_default_discount_reminder_email_template(self) -> str:
        """Alapértelmezett discount reminder email template"""
        return """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Kedvezményed hamarosan lejár!</title>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: #ffc107; color: #333; padding: 20px; text-align: center; }
        .content { padding: 20px; background: #f8f9fa; }
        .urgent-box { background: #fff3cd; border: 2px solid #ffc107; padding: 15px; margin: 20px 0; text-align: center; }
        .button { display: inline-block; background: #ffc107; color: #333; padding: 12px 24px; text-decoration: none; border-radius: 5px; font-weight: bold; }
        .footer { text-align: center; padding: 20px; color: #666; font-size: 12px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>⏰ Kedvezményed hamarosan lejár!</h1>
        </div>
        
        <div class="content">
            <p>Kedves {{ customer_name or 'Vásárló' }}!</p>
            
            <div class="urgent-box">
                <h3>🚨 Sürgős!</h3>
                <p>A <strong>{{ discount_code }}</strong> kedvezménykódod <strong>{{ valid_until|format_date('%Y.%m.%d %H:%M') }}</strong>-ig érvényes!</p>
                <p>Ez még {{ hours_left }} óra és {{ minutes_left }} perc!</p>
            </div>
            
            <p>Ne hagyd ki ezt a különleges lehetőséget! A kedvezményed {{ discount_percentage|format_percentage }} kedvezményt biztosít 
            {{ minimum_order_value|format_price }} feletti rendelésre.</p>
            
            <p style="text-align: center; margin: 30px 0;">
                <a href="{{ website_url }}/cart" class="button">Rendelés most!</a>
            </p>
        </div>
        
        <div class="footer">
            <p>{{ company_name }} | {{ website_url }}</p>
            <p>Email: {{ support_email }} | Tel: {{ support_phone }}</p>
            <p><a href="{{ website_url }}/unsubscribe">Leiratkozás</a></p>
        </div>
    </div>
</body>
</html>"""
    
    def _get_default_abandoned_cart_text_template(self) -> str:
        """Alapértelmezett abandoned cart text template"""
        return """Kedves {{ customer_name or 'Vásárló' }}!

Észrevettük, hogy a kosaradban {{ cart_items|length }} termék vár a megvásárlásra, 
összesen {{ formatted_cart_value }} értékben.

{% if cart_items %}
A kosaradban lévő termékek:
{% for item in cart_items %}
- {{ item.name }} ({{ item.quantity }} db) - {{ item.formatted_total_price }}
{% endfor %}
{% endif %}

{% if discount_code %}
🎁 Különleges kedvezmény!
Használd a {{ discount_code }} kódot és spórolj {{ discount_percentage|format_percentage }}-ot!
Kedvezmény érvényes: {{ valid_until|format_date('%Y.%m.%d') }}-ig
{% endif %}

Vissza a kosarhoz: {{ website_url }}/cart

Ha kérdésed van, ne habozz kapcsolatba lépni velünk!
{{ company_name }}
{{ website_url }}
Email: {{ support_email }} | Tel: {{ support_phone }}

Leiratkozás: {{ website_url }}/unsubscribe"""
    
    def _get_default_welcome_text_template(self) -> str:
        """Alapértelmezett welcome text template"""
        return """Kedves {{ customer_name or 'Vásárló' }}!

🎉 Köszönjük, hogy csatlakozott a ChatBuddy közösségéhez!

Most már részese a ChatBuddy közösségének, ahol:
- Gyors és szakmailag felkészült AI asszisztens segít a vásárlásban
- Különleges kedvezményeket és ajánlatokat kap
- Először értesül új termékekről és kampányokról

{% if welcome_discount %}
🎁 Üdvözlő ajánlat!
Használd a {{ welcome_discount }} kódot és spórolj {{ discount_percentage|format_percentage }}-ot az első rendelésedben!
{% endif %}

Böngészés kezdése: {{ website_url }}

{{ company_name }}
{{ website_url }}
Email: {{ support_email }} | Tel: {{ support_phone }}

Leiratkozás: {{ website_url }}/unsubscribe"""
    
    def _get_default_discount_reminder_text_template(self) -> str:
        """Alapértelmezett discount reminder text template"""
        return """Kedves {{ customer_name or 'Vásárló' }}!

⏰ Sürgős! A {{ discount_code }} kedvezménykódod {{ valid_until|format_date('%Y.%m.%d %H:%M') }}-ig érvényes!

Ez még {{ hours_left }} óra és {{ minutes_left }} perc!

Ne hagyd ki ezt a különleges lehetőséget! A kedvezményed {{ discount_percentage|format_percentage }} kedvezményt biztosít {{ minimum_order_value|format_price }} feletti rendelésre.

Rendelés most: {{ website_url }}/cart

{{ company_name }}
{{ website_url }}
Email: {{ support_email }} | Tel: {{ support_phone }}

Leiratkozás: {{ website_url }}/unsubscribe"""
    
    def _get_fallback_email_template(self, template_name: str, data: Dict[str, Any]) -> str:
        """Fallback email template hiba esetén"""
        return f"""<html><body>
<h1>Üzenet a {data.get('company_name', 'ChatBuddy')} csapatától</h1>
<p>Kedves {data.get('customer_name', 'Vásárló')}!</p>
<p>Ez egy automatikus üzenet. Kérjük, látogassa meg weboldalunkat: {data.get('website_url', 'https://chatbuddy.com')}</p>
<p>Üdvözlettel,<br>{data.get('company_name', 'ChatBuddy')} csapata</p>
</body></html>"""
    
    def _get_fallback_text_template(self, template_name: str, data: Dict[str, Any]) -> str:
        """Fallback text template hiba esetén"""
        return f"""Kedves {data.get('customer_name', 'Vásárló')}!

Ez egy automatikus üzenet. Kérjük, látogassa meg weboldalunkat: {data.get('website_url', 'https://chatbuddy.com')}

Üdvözlettel,
{data.get('company_name', 'ChatBuddy')} csapata"""
    
    def _get_fallback_sms_template(self, template_name: str, data: Dict[str, Any]) -> str:
        """Fallback SMS template hiba esetén"""
        return f"""Kedves {data.get('customer_name', 'Vásárló')}!

Ez egy automatikus üzenet a {data.get('company_name', 'ChatBuddy')} csapatától.

További információ: {data.get('website_url', 'https://chatbuddy.com')}"""
