## Async & Concurrency

### Async/Await Usage
- **Priority**: PREFERRED
- **Pattern**: Uses async/await for I/O-bound operations (LLM API calls)
- **Examples**:
  ```python
  async def _perform_async_inference(llm: Runnable[LanguageModelInput, BaseMessage],
                                      batched_tasks: List[InferenceRequest]) -> List[InferenceResult]:
      async_responses = [llm.ainvoke(task.context) for task in batched_tasks]
      responses = await asyncio.gather(*async_responses)
      return [InferenceResult(task_id=task.task_id, response=response)
              for task, response in zip(batched_tasks, responses)]
  ```

### Async Wrapper Pattern
- **Priority**: PREFERRED
- **Pattern**: Sync wrapper function calls `asyncio.run()` for async implementation
- **Examples**:
  ```python
  def perform_inference(llm: Runnable[LanguageModelInput, BaseMessage],
                        batched_tasks: List[InferenceRequest]) -> List[InferenceResult]:
      return asyncio.run(_perform_async_inference(llm, batched_tasks))
  ```

