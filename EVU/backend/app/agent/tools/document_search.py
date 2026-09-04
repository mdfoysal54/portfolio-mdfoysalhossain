from sqlalchemy.orm import Session

from app.agent.tools.base import ToolExecution
from app.schemas.document import RAGSource
from app.services.rag_service import rag_service


class DocumentSearchTool:
    name = "document_search"

    async def run(self, user_id: int, query: str, db: Session) -> tuple[ToolExecution, list[RAGSource]]:
        results = await rag_service.retrieve(user_id, query, db)
        if not results:
            return (
                ToolExecution(
                    name=self.name,
                    input=query,
                    output="No relevant uploaded document content was found.",
                    success=True,
                ),
                [],
            )

        lines = []
        sources = []
        for item in results:
            lines.append(
                f"[{item.filename} | chunk {item.chunk_index + 1} | score {item.score:.3f}]\n{item.content}"
            )
            sources.append(
                RAGSource(
                    document_id=item.document_id,
                    filename=item.filename,
                    chunk_index=item.chunk_index,
                    score=item.score,
                )
            )

        output = rag_service.build_context(results)
        if not output:
            output = "\n\n".join(lines)

        return (
            ToolExecution(
                name=self.name,
                input=query,
                output=output,
                success=True,
            ),
            sources,
        )


document_search_tool = DocumentSearchTool()