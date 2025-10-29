# photographers
A web platform for Rwandan photographers to showcase work, manage bookings, and connect with clients.  Photographers management system built with Django, empowering Rwanda’s creative community.  A platform for managing photography portfolios, bookings, and payments in Rwanda.


## Logo Setup

Your photography platform includes a logo management system. Follow the instructions below to add, validate and activate a logo for the site.

### What was added

- A logo directory: `static/images/logos/`
- Helper CSS: `static/css/logo-styles.css`
- Helper JS: `static/js/logo-manager.js`
- A Django management command: `manage_logos` (list/validate/activate)
- Template support and fallback in `templates/base.html`

### Quick Setup

1. Copy your logo file into `static/images/logos/` (recommended: PNG or SVG, ~200x50px, transparent background).
2. Activate it with the management command:

```powershell
cd "c:\Users\user\Desktop\All Folders\Photographers"
python manage.py manage_logos --activate your-logo-filename.png
```

3. Restart the server and verify the logo displays (or update `templates/base.html` manually to point to the file).

### Useful commands

```powershell
# List available logos
python manage.py manage_logos --list

# Validate a logo file
python manage.py manage_logos --validate your-logo-filename.png

# Activate a logo
python manage.py manage_logos --activate your-logo-filename.png
```

For full details (examples, troubleshooting and advanced options) see `LOGO_SETUP_GUIDE.md` in the repository. After you confirm the README contains everything you need, you can safely delete `LOGO_SETUP_GUIDE.md`.
