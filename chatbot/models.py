from django.db import models
from django.utils.encoding import python_2_unicode_compatible


@python_2_unicode_compatible
class Message(models.Model):
    market = models.CharField(
        max_length=20,
    )
    text = models.CharField(
        max_length=64,
    )
    incoming = models.BooleanField(
        blank=True,
        default=False,
    )
    price = models.DecimalField(max_digits=19, decimal_places=10)
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
    )

    class Meta:
        app_label = 'chatbot'
        verbose_name = 'Message'

    def __str__(self):
        return "{}: {}".format(self.market, self.text)

