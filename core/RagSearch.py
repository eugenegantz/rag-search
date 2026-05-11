import json
import logging
from datetime import datetime
from openai import OpenAI

from core.readers.ChunkReaderFactory import ChunkReaderFactory
from core.readers.BaseChunkReader import BaseChunkReader, TChunkArgs
from core.types import TRagSearchResult, TContextEntry, TCDBMetaEntry, TConfigOpenAI
from core.ResourceIndexer import ResourceIndexer


TEST_RESPONSE = """
В компании Яндекс используются плагины и утилиты командной строки для работы с ИИ, в частности continue и Open CД. Также есть инструмент развёртывания и настройки кодовых ассистентов, позволяющий по кнопке развернуть текущую конфигурацию с доступом к внутренним моделям. Популярным продуктом является автоматическая ревью кода, интегрированная с GitLab: при создании merge request асинхронно запускается ревью, результаты появляются в комментариях [^yandex_01].

Доступ к моделям осуществляется не напрямую, а через прокси (LM gateway). Пользователей переводят на модель по сценарию: модель для агентского кодинга, большая модель для сложных задач, маленькая для написания тестов и простых задач, модель для доступа по API или в чате. Через прокси также реализуется лимитирование вычислений токенов, настройка моделей под сценарий и сбор аналитики [^yandex_01].

Агентским кодовым ассистентом пользуется порядка 1100 человек в день, примерно 25-30% используют его ежедневно. После перехода на Minimк плюс Open Code Cline наблюдался резкий рост адопшена. К ревью кода подключено около полутора тысяч проектов [^yandex_01].

В Яндексе доступен широкий диапазон моделей — от больших известных до китайских, развёрнутых на собственном железе. Есть рекомендации от СИБОв и правила, каким моделям можно передавать данные. Для задач без конфиденциальной информации используются личные подписки на лучшие модели. Для кода ситуация сложнее из-за массовости использования и стоимости топовых моделей, поэтому проводятся собственные бенчмарки для оценки окупаемости [^yandex_03].

Обсуждается проект «Железного джуна» — автономный агент для выполнения простых задач масштаба джуна без необходимости постоянного контроля. Аналогичный опубликованный кейс — Stripe Minions, где автономный агент берёт задачу и возвращается с пулреквестом [^yandex_03].

Высказывается мнение, что ИИ не заменит людей, а заменит тех, кто не умеет им пользоваться. Отмечается парадокс: чем больше человек использует ИИ, тем больше он работает и быстрее выгорает [^yandex_03].

Егор Бугаенко (yegor256) считает, что 95% программистов станут «кодерами», не понимающими базовых основ, но использующими инструменты вроде Cursor или Claude Code, а 5% станут высокооплачиваемой элитой с глубокими знаниями. Он также отмечает, что создание сложного софта (вроде Photoshop) теперь возможно за неделю одному кодеру с ИИ вместо многолетней работы тысяч программистов [^yegor256_02].

При выборе между теоретически подкованным программистом и практиком, который просто хорошо пишет (возможно с ИИ), предпочтение отдаётся практику для выполнения задач, а теоретик — для ранних стадий проекта и архитектурных обсуждений [^yegor256_03].

По поводу распространения знаний об ИИ в команде: если компания чужая — не делиться, показывать хорошие результаты молча; если своя — делиться. Отмечается, что многие до сих пор не знают о возможностях ИИ или не имеют к ним доступа [^yegor256_03].

В корпоративном управлении выделяются «красные» (максимально лояльные начальству) и «чёрные» (ориентированные на общее дело) сотрудники. Рекомендуется не спрашивать разрешения на использование ИИ-инструментов у начальства, а просто делать, опираясь на собственное понимание целесообразности [^yegor256_05].

Высказывается убеждение, что программисты уже не смогут работать без ИИ-инструментов вроде Claude Code, а те, кто не адаптируется, переквалифицируются. Новый кризис — не в доступе к инструментам, а в постановке задач: с появлением мощных ИИ открываются возможности, которые раньше казались недостижимыми [^yegor256_05].

Обсуждаются риски утечки данных через ИИ-инструменты: примеры запрета использования GitHub Copilot в Microsoft и увольнения сотрудников Samsung за слив кодовой базы в ChatGPT. Рекомендуется быть осторожными с конфиденциальным кодом, особенно при конкуренции с Microsoft [^yandex_02].

В контексте TypeScript и браузеров обсуждается, что добавление TypeScript напрямую в браузер увеличит объём поддерживаемого кода без очевидной выгоды. Разработчикам браузеров нужно 5-8 лет, чтобы TypeScript стал стандартом в индустрии [^yandex_02].

[{"id":"yandex_01","filepath":"q:\\\\_PROJ\\\\rag-test-01\\\\test_data\\\\yandex_01.txt","note":"Инструменты ИИ в Яндексе: плагины, ревью кода, прокси для моделей, статистика использования"},{"id":"yandex_03","filepath":"q:\\\\_PROJ\\\\rag-test-01\\\\test_data\\\\yandex_03.txt","note":"Модели в Яндексе, проект Железного джуна, выгорание от ИИ"},{"id":"yegor256_02","filepath":"q:\\\\_PROJ\\\\rag-test-01\\\\test_data\\\\yegor256_02.txt","note":"Прогноз о 95% кодеров и 5% элиты, дешевизна софта с ИИ"},{"id":"yegor256_03","filepath":"q:\\\\_PROJ\\\\rag-test-01\\\\test_data\\\\yegor256_03.txt","note":"Выбор между теоретиком и практиком, дилемма распространения знаний об ИИ"},{"id":"yegor256_05","filepath":"q:\\\\_PROJ\\\\rag-test-01\\\\test_data\\\\yegor256_05.txt","note":"Красные и чёрные сотрудники, невозможность возврата к работе без ИИ"},{"id":"yandex_02","filepath":"q:\\\\_PROJ\\\\rag-test-01\\\\test_data\\\\yandex_02.txt","note":"Риски утечек данных, TypeScript в браузерах"}]
"""


SYSTEM_PROMPT_TEMPLATE = """
# РОЛЬ
Ты — профессиональный ассистент, который дает ответы строго на основе предоставленного КОНТЕКСТА.

# ПРАВИЛА РАБОТЫ
- Используй ТОЛЬКО информацию из блока КОНТЕКСТ ниже.
- Если в КОНТЕКСТЕ нет прямого ответа на вопрос, честно ответь: "К сожалению, в предоставленных документах нет информации об этом". Не используй свои фоновые знания.
- Если ответ есть, пиши кратко, по делу и сохраняй терминологию оригинала.
- В конце ответа в последней строке укажи ссылки на документы на которые ты опирался. Ссылки укажи в порядке упоминания одной строкой в json-формате вида: [{{"id":"ID_ССЫЛКИ","filepath":"ПУТЬ_К_ФАЙЛУ","note":"ПРИМЕЧАНИЕ"}}, ...]. Не заключай json ни в какие дополнительные кавычки или символы — так, чтобы можно было прочитать последнюю строку и передать её в JSON.parse().
- В конца каждого параграфа укажи ссылку на источник. Ссылку запиши в формате: [^ID_ССЫЛКИ]. Если ссылок больше одной, то в формате: [^ID_ССЫЛКИ_1]...[^ID_ССЫЛКИ_N]. Где ID_ССЫЛКИ — это ID_ССЫЛКИ из json.

# КОНТЕКСТ
{context}

# ВОПРОС ПОЛЬЗОВАТЕЛЯ
{query}
"""


def context_to_string(context_arr: list[TContextEntry]) -> str:
    """Получить контекст как единую строку для вставки в промпт."""
    context_str = ""
    for ctx in context_arr:
        context_str += f"Источник: {ctx['filepath']}\n"
        context_str += ctx["content"] + "\n\n"
    return context_str.strip()


class RagSearch:
    def __init__(
        self, 
        resource_indexer: ResourceIndexer,
        openai_config: TConfigOpenAI,
        logger: logging.Logger | None = None,
    ):
        self.resource_indexer = resource_indexer
        self.logger = logger
        self.openai_config = openai_config


    def parse_result(self, result: str) -> TRagSearchResult:
        """Парсит ответ LLM: отделяет markdown от JSON-ссылок."""

        lines = result.splitlines()
        
        try:
            refsjson = lines.pop(-1)
            refs_list = json.loads(refsjson)

        except Exception as err:
            if self.logger:
                self.logger.error({
                    "event": "parse-rag-result-error",
                    "error": str(err),
                    "datetime": str(datetime.now()),
                })

            raise err
        
        return {
            "content": "\n".join(lines),
            "refs": refs_list,
        }


    def search(
        self,
        query: str,
        n_results: int = 10,
    ) -> TRagSearchResult:
        """Выполнить RAG-поиск: найти контекст + сгенерировать ответ LLM."""

        if "__TEST_RESPONSE__" == query:
            return self.parse_result(TEST_RESPONSE)

        context_arr = self.fetch_context(query, n_results)
        context = context_to_string(context_arr).strip()
        
        if not context:
            raise Exception("В индексе нет записей")
        
        prompt = SYSTEM_PROMPT_TEMPLATE.format(context=context, query=query)
        
        if "__TEST_RETURN_PROMPT__" == query:
            return {
                "content": prompt,
                "refs": [],
            }

        client = OpenAI(
            base_url=self.openai_config["base_url"],
            api_key=self.openai_config["api_key"],
            default_headers=self.openai_config.get("default_headers"),
        )
        
        res = client.chat.completions.create(
            model="kimi-for-coding",
            messages=[{"role": "user", "content": prompt}],
            extra_body={"thinking": {"type": "disabled"}},
        )

        # ПРИМЕР ОТВЕТА:
        #
        # ChatCompletion(
        #     id='chatcmpl-hFj...',
        #     choices=[
        #         Choice(
        #             finish_reason='stop',
        #             index=0,
        #             logprobs=None,
        #             message=ChatCompletionMessage(
        #                 content='abc ... [^ref_01].\n\n[{"id":"ref_01","filepath":"....","note":"..."}, ...]',
        #                 refusal=None,
        #                 role='assistant',
        #                 annotations=None,
        #                 audio=None,
        #                 function_call=None,
        #                 tool_calls=None
        #             )
        #         )
        #     ],
        #     created=1778618709,
        #     model='...',
        #     object='chat.completion',
        #     service_tier=None,
        #     system_fingerprint=None,
        #     usage=CompletionUsage(
        #         completion_tokens=672,
        #         prompt_tokens=4465,
        #         total_tokens=5137,
        #         completion_tokens_details=None,
        #         prompt_tokens_details=PromptTokensDetails(
        #             audio_tokens=None,
        #             cached_tokens=4465
        #         ),
        #         cached_tokens=4465
        #     )
        # )
        
        content = res.choices[0].message.content or ""

        if self.logger:
            self.logger.info({
                "event": "rag-search",
                "context_length": len(context),
                "prompt_length": len(prompt),
                "content_length": len(content),
                "datetime": str(datetime.now()),
            })
        
        return self.parse_result(content)


    def fetch_context(
        self,
        query: str,
        n_results: int = 10,
    ) -> list[TContextEntry]:
        """Найти релевантные контексты по запросу."""

        outputs = self.resource_indexer.pipe(query)[0][0]

        results = self.resource_indexer.collection.query(
            query_embeddings=[outputs],
            n_results=n_results,
        )

        metas:      list[TCDBMetaEntry]             = results["metadatas"][0] or []
        file_metas: dict[str, list[TChunkArgs]]     = {}
        context:    list[TContextEntry]             = []

        for meta in metas:
            filepath = meta.get("filepath", "")
            if not filepath:
                continue

            if filepath not in file_metas:
                file_metas[filepath] = []

            file_metas[filepath].append({
                "from": meta["from"],
                "to": meta["to"],
            })

        _readers: dict[str, BaseChunkReader] = dict()

        for filepath, meta_list in file_metas.items():
            reader = _readers.get(filepath, None)

            if not reader:
                reader = ChunkReaderFactory.get_reader(filepath)
                _readers[filepath] = reader

            chunks = reader.getChunks(meta_list)

            content = "\n\n".join(chunk["text"] for chunk in chunks)

            context.append({
                "filepath": filepath,
                "content": content,
            })

        context.sort(key=lambda row: row["filepath"])

        return context