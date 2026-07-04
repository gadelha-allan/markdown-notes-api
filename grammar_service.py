from fastapi import HTTPException

tool = None

def get_grammar_tool():
    global tool
    if tool is None:
        try:
            import language_tool_python
            tool = language_tool_python.LanguageTool('pt-BR')
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Erro ao inicializar o serviço de gramática (certifique-se de ter o Java instalado): {str(e)}"
            )
    return tool