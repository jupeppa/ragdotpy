SUMMARY_PROMPT = """Based on the conversation history below, provide a brief 1-2 sentence summary.
                Answer in the specified language: {language}
                
                Conversation:
                {conversation_context}
                """

FULL_RESPONSE_PROMPT = """You are a helpful and informative bot that answers questions using the reference passages and conversation history included below.
                Be sure to respond in a complete sentence, being comprehensive, including all relevant background information.
                If the passages are irrelevant to the answer, you may ignore them. Answer in the specified language: {language}
                
                Previous Conversation:
                {conversation_context}
                
                Reference Passages:
                {reference_context}
                
                Current Question: {query}
                """