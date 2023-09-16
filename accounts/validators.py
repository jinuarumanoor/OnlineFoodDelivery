from django.core.exceptions import ValidationError
import os



def allow_only_images_validator(value):
    ext = os.path.splitext(value.name)[1]  # [0] returns path+filename
    print(ext)
    valid_extensions = ['.jpg', '.jpeg', '.png']
    if not ext.lower() in valid_extensions:
        raise ValidationError('Unsupported file extension.Allowed Extensions' +str(valid_extensions))
    