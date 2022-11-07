class JobHelper():
    @staticmethod
    def make_filter(*args) -> 'str | None':
        """
        Создать фильтр используя заданные.
        """
        if args:
            return '&'.join(arg for arg in args if arg)
        return None
        