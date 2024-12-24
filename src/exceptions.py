class ParserFindTagException(Exception):
    """Кастомное исключение для ошибок при поиске тега."""

    pass


class VersionsNotFound(Exception):
    """Исключение, выбрасываемое, если список версий Python не найден."""

    pass
