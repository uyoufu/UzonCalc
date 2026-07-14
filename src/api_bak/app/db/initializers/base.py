from sqlalchemy.ext.asyncio import AsyncSession


class BaseInitializer:
    async def initialize(self, session: AsyncSession):
        raise NotImplementedError("Subclasses must implement this method")
