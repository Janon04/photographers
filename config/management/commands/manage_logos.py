import os
from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    help = 'Manage company logos - list, validate, and set active logos'

    def add_arguments(self, parser):
        parser.add_argument(
            '--list',
            action='store_true',
            help='List all available logo files',
        )
        parser.add_argument(
            '--validate',
            type=str,
            help='Validate a specific logo file',
        )
        parser.add_argument(
            '--activate',
            type=str,
            help='Set a logo as active by updating the template',
        )

    def handle(self, *args, **options):
        logo_dir = os.path.join(settings.BASE_DIR, 'static', 'images', 'logos')
        
        if options['list']:
            self.list_logos(logo_dir)
        elif options['validate']:
            self.validate_logo(logo_dir, options['validate'])
        elif options['activate']:
            self.activate_logo(options['activate'])
        else:
            self.stdout.write(self.style.SUCCESS('Logo Management Commands:'))
            self.stdout.write('  --list: List all available logos')
            self.stdout.write('  --validate filename: Check if logo file is valid')
            self.stdout.write('  --activate filename: Set logo as active')

    def list_logos(self, logo_dir):
        """List all logo files"""
        if not os.path.exists(logo_dir):
            self.stdout.write(self.style.ERROR(f'Logo directory not found: {logo_dir}'))
            return

        logo_files = []
        for file in os.listdir(logo_dir):
            if file.lower().endswith(('.png', '.jpg', '.jpeg', '.svg', '.webp')):
                file_path = os.path.join(logo_dir, file)
                file_size = os.path.getsize(file_path)
                logo_files.append((file, file_size))

        if not logo_files:
            self.stdout.write(self.style.WARNING('No logo files found'))
            return

        self.stdout.write(self.style.SUCCESS('Available Logo Files:'))
        for filename, size in logo_files:
            size_kb = round(size / 1024, 2)
            self.stdout.write(f'  📄 {filename} ({size_kb} KB)')

    def validate_logo(self, logo_dir, filename):
        """Validate a logo file"""
        file_path = os.path.join(logo_dir, filename)
        
        if not os.path.exists(file_path):
            self.stdout.write(self.style.ERROR(f'File not found: {filename}'))
            return

        # Check file size
        file_size = os.path.getsize(file_path)
        size_kb = round(file_size / 1024, 2)
        
        self.stdout.write(self.style.SUCCESS(f'Logo Validation for: {filename}'))
        self.stdout.write(f'  📊 File size: {size_kb} KB')
        
        if size_kb > 500:
            self.stdout.write(self.style.WARNING('  ⚠️  Large file size (>500KB), consider optimizing'))
        else:
            self.stdout.write(self.style.SUCCESS('  ✅ Good file size'))

        # Check file extension
        valid_extensions = ['.png', '.jpg', '.jpeg', '.svg', '.webp']
        file_ext = os.path.splitext(filename)[1].lower()
        
        if file_ext in valid_extensions:
            self.stdout.write(self.style.SUCCESS(f'  ✅ Valid format: {file_ext}'))
        else:
            self.stdout.write(self.style.ERROR(f'  ❌ Invalid format: {file_ext}'))

    def activate_logo(self, filename):
        """Update the template to use the specified logo"""
        template_path = os.path.join(settings.BASE_DIR, 'templates', 'base.html')
        
        if not os.path.exists(template_path):
            self.stdout.write(self.style.ERROR('Base template not found'))
            return

        # Read the template
        with open(template_path, 'r', encoding='utf-8') as file:
            content = file.read()

        # Create the new logo line
        new_logo_line = f'                <img src="{{% static \'images/logos/{filename}\' %}}" alt="Company Logo" class="logo-image">'
        
        # Find and replace the logo section
        import re
        
        # Pattern to find the commented logo line
        pattern = r'(\s*)<!-- <img src="[^"]*" alt="[^"]*" class="logo-image"> -->'
        
        if re.search(pattern, content):
            # Replace commented line with active logo
            content = re.sub(pattern, f'\\1{new_logo_line}', content)
            self.stdout.write(self.style.SUCCESS('Updated commented logo line'))
        else:
            # Look for existing active logo line
            existing_pattern = r'(\s*)<img src="[^"]*logos/[^"]*" alt="[^"]*" class="logo-image">'
            if re.search(existing_pattern, content):
                content = re.sub(existing_pattern, f'\\1{new_logo_line}', content)
                self.stdout.write(self.style.SUCCESS('Updated existing logo'))
            else:
                self.stdout.write(self.style.WARNING('Could not find logo section to update'))
                self.stdout.write('Please manually update the base.html template')
                return

        # Write the updated content
        with open(template_path, 'w', encoding='utf-8') as file:
            file.write(content)

        self.stdout.write(self.style.SUCCESS(f'✅ Logo activated: {filename}'))
        self.stdout.write('🔄 Please restart your Django server to see changes')