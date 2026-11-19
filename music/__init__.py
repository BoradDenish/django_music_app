# Python 3.14 compatibility patch for Django Context copying in tests/templates
import django.template.context as _dj_ctx

if not hasattr(_dj_ctx.BaseContext, '_py314_patched'):
    def _base_context_copy(self):
        duplicate = self.__class__.__new__(self.__class__)
        duplicate.__dict__.update(self.__dict__)
        duplicate.dicts = self.dicts[:]
        return duplicate

    _dj_ctx.BaseContext.__copy__ = _base_context_copy
    _dj_ctx.BaseContext._py314_patched = True
