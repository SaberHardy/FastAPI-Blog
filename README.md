Run Server
> 
> fastapi dev main.py
> 
or to avoid restarting the server on every change, you can use
> uvicorn main:app --reload

> 
> Libraries need to be Installed
> 1. uv add sqlalchemy
> 2. pip3 install sqlalchemy
> 
>

> Async vs Sync
> 
> So, async allows your program to handle multiple tasks concurrently. In my async IO video, I compared this to a McDonald's versus a Subway. With synchronous code execution, which is what we normally write, one thing happens after another. 

> So, it's like going to a Subway restaurant where they make your entire sandwich from start to finish before moving on to the next customer. But in concurrent code, in asynchronous code, it's more like a McDonald's where someone takes your order and then moves on to the next customer while your food is being made in the background.
> Async does not help with computing or CPU-bound operations. So those would be things like:
> - "heavy calculations" 
> - "image processing"
> - "data crunching"
> 
> These keep the CPU busy doing actual work. 
> 
> So there's no waiting actually involved there. 
> So there's nothing for `async` to optimize. `async` isn't always faster. That's a common misconception. 
> For simple fast queries, you might not see much benefit. The overhead of the `Async` machinery can even slow things down slightly. 
> Now the real benefits show up when you have a `concurrent load`, meaning a lot of requests happening at the same time. 