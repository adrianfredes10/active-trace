"""Cliente de envío de correo — C-12 (stub para tests y dev)."""


class MailDeliveryError(Exception):
    pass


class MailSender:
    async def send(self, *, destinatario: str, asunto: str, cuerpo: str) -> None:
        if destinatario.endswith("@fail.example.com"):
            raise MailDeliveryError(f"No se pudo entregar a {destinatario}")
