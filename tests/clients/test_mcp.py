from types import SimpleNamespace

import anyio
import pytest

import axiv.clients.mcp as mcp_client_module
from axiv.clients.mcp import McpClient
from axiv.errors import InputError
from axiv.errors import PermissionDeniedError
from axiv.errors import RemoteAPIError
from axiv.models.mcp import AnswerPdfQueriesArguments
from axiv.models.mcp import CreateFolderArguments
from axiv.models.mcp import DeleteFolderArguments
from axiv.models.mcp import DiscoverPapersArguments
from axiv.models.mcp import GetPaperContentArguments
from axiv.models.mcp import GithubRepositoryArguments
from axiv.models.mcp import ListLibraryArguments
from axiv.models.mcp import MovePapersArguments
from axiv.models.mcp import RemovePapersArguments
from axiv.models.mcp import RenameFolderArguments
from axiv.models.mcp import SavePapersArguments


class FakeStreamContext:
    def __init__(self) -> None:
        self.closed = False

    async def __aenter__(self) -> tuple[object, object, None]:
        return object(), object(), None

    async def __aexit__(self, *_args: object) -> None:
        self.closed = True


class FakeSession:
    def __init__(self) -> None:
        self.closed = False
        self.initialize_calls = 0
        self.call_result: object = SimpleNamespace(
            content=[SimpleNamespace(type="text", text="first"), SimpleNamespace(type="text", text="second")],
            isError=False,
            structuredContent={"requestId": "request-1"},
        )
        self.calls: list[tuple[str, dict[str, object]]] = []
        self.results_by_tool: dict[str, object] = {}

    async def initialize(self) -> object:
        self.initialize_calls += 1
        return SimpleNamespace(
            protocolVersion="2025-03-26",
            serverInfo=SimpleNamespace(name="alphaXiv", version="1.0"),
        )

    async def list_tools(self) -> object:
        return SimpleNamespace(
            tools=[
                SimpleNamespace(
                    name="discover_papers",
                    description="Discover papers",
                    inputSchema={
                        "type": "object",
                        "properties": {"question": {"type": "string"}},
                        "required": ["question"],
                    },
                )
            ]
        )

    async def call_tool(self, name: str, arguments: dict[str, object]) -> object:
        self.calls.append((name, arguments))
        return self.results_by_tool.get(name, self.call_result)


class FakeSessionContext:
    def __init__(self, session: FakeSession) -> None:
        self.session = session

    async def __aenter__(self) -> FakeSession:
        return self.session

    async def __aexit__(self, *_args: object) -> None:
        self.session.closed = True


def make_client(
    monkeypatch: pytest.MonkeyPatch,
    *,
    session: FakeSession | None = None,
) -> tuple[McpClient, FakeStreamContext, FakeSession, list[tuple[str, dict[str, str]]]]:
    monkeypatch.setenv("ALPHAXIV_API_KEY", "axv-test-secret")
    stream_context = FakeStreamContext()
    fake_session = session or FakeSession()
    stream_calls: list[tuple[str, dict[str, str]]] = []

    def stream_factory(url: str, *, headers: dict[str, str]) -> FakeStreamContext:
        stream_calls.append((url, headers))
        return stream_context

    def session_factory(_read: object, _write: object) -> FakeSessionContext:
        return FakeSessionContext(fake_session)

    client = McpClient(_stream_factory=stream_factory, _session_factory=session_factory)
    return client, stream_context, fake_session, stream_calls


def test_missing_api_key_is_rejected_before_transport(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ALPHAXIV_API_KEY", raising=False)

    with pytest.raises(InputError, match="ALPHAXIV_API_KEY"):
        McpClient()


def test_fixed_endpoint_bearer_header_and_initialize_result(monkeypatch: pytest.MonkeyPatch) -> None:
    client, stream, session, stream_calls = make_client(monkeypatch)

    async def scenario() -> None:
        async with client:
            result = await client.initialize()
            assert result.protocol_version == "2025-03-26"
            assert result.server_name == "alphaXiv"

    anyio.run(scenario)

    assert stream_calls == [
        (
            "https://api.alphaxiv.org/mcp/v1",
            {"Authorization": "Bearer axv-test-secret"},
        )
    ]
    assert session.initialize_calls == 1
    assert session.closed is True
    assert stream.closed is True


def test_list_tools_returns_typed_names_and_required_schema(monkeypatch: pytest.MonkeyPatch) -> None:
    client, _, _, _ = make_client(monkeypatch)

    async def scenario() -> None:
        async with client:
            await client.initialize()
            result = await client.list_tools()
        assert result.tools[0].name == "discover_papers"
        assert result.tools[0].required_arguments == ("question",)

    anyio.run(scenario)


def test_tool_text_content_is_combined_without_losing_metadata(monkeypatch: pytest.MonkeyPatch) -> None:
    client, _, session, _ = make_client(monkeypatch)
    arguments = DiscoverPapersArguments(
        question="Which papers explain attention?",
        keywords=("attention",),
        difficulty=5,
    )

    async def scenario() -> None:
        async with client:
            await client.initialize()
            result = await client.discover_papers(arguments)
        assert result.text == "first\nsecond"
        assert result.is_error is False
        assert result.metadata == {"requestId": "request-1"}

    anyio.run(scenario)

    assert session.calls == [
        (
            "discover_papers",
            {
                "keywords": ["attention"],
                "question": "Which papers explain attention?",
                "difficulty": 5.0,
            },
        )
    ]


def test_each_public_method_dispatches_one_fixed_tool(monkeypatch: pytest.MonkeyPatch) -> None:
    client, _, session, _ = make_client(monkeypatch)
    session.results_by_tool["list_library"] = SimpleNamespace(
        content=[SimpleNamespace(type="text", text='{"folders": []}')],
        isError=False,
        structuredContent=None,
    )
    mutation_result = SimpleNamespace(
        content=[SimpleNamespace(type="text", text='{"count": 1}')],
        isError=False,
        structuredContent=None,
    )
    for tool in (
        "save_papers_to_folder",
        "remove_papers_from_folder",
        "move_papers_between_folders",
        "create_folder",
        "rename_folder",
        "delete_folder",
    ):
        session.results_by_tool[tool] = mutation_result

    async def scenario() -> None:
        async with client:
            await client.initialize()
            await client.discover_papers(
                DiscoverPapersArguments(keywords=("attention",), question="Question", difficulty=3)
            )
            await client.get_paper_content(GetPaperContentArguments(url="https://arxiv.org/abs/1706.03762"))
            await client.answer_pdf_queries(
                AnswerPdfQueriesArguments(paper="1706.03762", queries=("What is the method?",))
            )
            await client.read_github_files(
                GithubRepositoryArguments(githubUrl="https://github.com/owner/repo", path="/")
            )
            await client.list_library(ListLibraryArguments())
            await client.save_papers(SavePapersArguments(folder_id="folder-1", paper_ids_or_urls=("1706.03762",)))
            await client.remove_papers(RemovePapersArguments(folder_id="folder-1", paper_ids_or_urls=("1706.03762",)))
            await client.move_papers(
                MovePapersArguments(
                    from_folder_id="folder-1",
                    to_folder_id="folder-2",
                    paper_ids_or_urls=("1706.03762",),
                )
            )
            await client.create_folder(CreateFolderArguments(name="Reading"))
            await client.rename_folder(RenameFolderArguments(folder_id="folder-1", name="Read next"))
            await client.delete_folder(DeleteFolderArguments(folder_id="folder-1"))

    anyio.run(scenario)

    assert [name for name, _ in session.calls] == [
        "discover_papers",
        "get_paper_content",
        "answer_pdf_queries",
        "read_files_from_github_repository",
        "list_library",
        "save_papers_to_folder",
        "remove_papers_from_folder",
        "move_papers_between_folders",
        "create_folder",
        "rename_folder",
        "delete_folder",
    ]


def test_tool_error_is_mapped_without_disclosing_structured_payload(monkeypatch: pytest.MonkeyPatch) -> None:
    session = FakeSession()
    session.call_result = SimpleNamespace(
        content=[SimpleNamespace(type="text", text="Quota exhausted\x1b[31m")],
        isError=True,
        structuredContent={"apiKey": "axv-private"},
    )
    client, _, _, _ = make_client(monkeypatch, session=session)

    async def scenario() -> None:
        async with client:
            await client.initialize()
            with pytest.raises(RemoteAPIError, match="Quota exhausted") as captured:
                await client.discover_papers(
                    DiscoverPapersArguments(keywords=("topic",), question="Question", difficulty=1)
                )
            assert "axv-private" not in str(captured.value)
            assert "\x1b" not in str(captured.value)

    anyio.run(scenario)


def test_session_and_stream_close_when_initialization_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    class FailingSession(FakeSession):
        async def initialize(self) -> object:
            raise RuntimeError("private protocol detail")

    session = FailingSession()
    client, stream, fake_session, _ = make_client(monkeypatch, session=session)

    async def scenario() -> None:
        with pytest.raises(RemoteAPIError, match="MCP initialization failed") as captured:
            async with client:
                await client.initialize()
        assert "private protocol detail" not in str(captured.value)

    anyio.run(scenario)

    assert fake_session.closed is True
    assert stream.closed is True


def test_production_transport_preflight_preserves_authentication_status(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ALPHAXIV_API_KEY", "axv-test-secret")

    class FakeHttpClient:
        follow_redirects = True

        async def __aenter__(self) -> "FakeHttpClient":
            return self

        async def __aexit__(self, *_args: object) -> None:
            return None

        async def head(self, url: str) -> object:
            assert url == "https://api.alphaxiv.org/mcp/v1"
            assert self.follow_redirects is False
            return SimpleNamespace(status_code=401)

    fake_http = FakeHttpClient()
    monkeypatch.setattr(mcp_client_module, "create_mcp_http_client", lambda headers: fake_http)

    async def scenario() -> None:
        client = McpClient()
        with pytest.raises(PermissionDeniedError, match="MCP authentication failed"):
            async with client:
                pass

    anyio.run(scenario)


def test_transport_authentication_failure_is_mapped_and_client_is_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ALPHAXIV_API_KEY", "axv-test-secret")

    class AuthenticationError(Exception):
        def __init__(self) -> None:
            self.response = SimpleNamespace(status_code=401)
            super().__init__("remote detail with axv-test-secret")

    class FailingStreamContext(FakeStreamContext):
        async def __aenter__(self) -> tuple[object, object, None]:
            raise AuthenticationError

    def stream_factory(_url: str, *, headers: dict[str, str]) -> FailingStreamContext:
        assert headers["Authorization"] == "Bearer axv-test-secret"
        return FailingStreamContext()

    client = McpClient(_stream_factory=stream_factory)

    async def scenario() -> None:
        with pytest.raises(PermissionDeniedError, match="MCP authentication failed") as captured:
            async with client:
                pass
        assert "axv-test-secret" not in str(captured.value)
        with pytest.raises(RuntimeError, match="cannot be reused"):
            async with client:
                pass

    anyio.run(scenario)


def test_authentication_status_is_mapped_without_remote_details(monkeypatch: pytest.MonkeyPatch) -> None:
    class AuthenticationError(Exception):
        def __init__(self) -> None:
            self.response = SimpleNamespace(status_code=403)
            super().__init__("remote detail with axv-private")

    class FailingSession(FakeSession):
        async def initialize(self) -> object:
            raise AuthenticationError

    client, _, _, _ = make_client(monkeypatch, session=FailingSession())

    async def scenario() -> None:
        async with client:
            with pytest.raises(PermissionDeniedError, match="MCP authentication failed") as captured:
                await client.initialize()
            assert "axv-private" not in str(captured.value)

    anyio.run(scenario)


def test_plain_text_mutation_result_is_reported_without_retry_risk(monkeypatch: pytest.MonkeyPatch) -> None:
    client, _, session, _ = make_client(monkeypatch)
    session.results_by_tool["create_folder"] = SimpleNamespace(
        content=[SimpleNamespace(type="text", text="Folder created")],
        isError=False,
        structuredContent=None,
    )

    async def scenario() -> None:
        async with client:
            await client.initialize()
            result = await client.create_folder(CreateFolderArguments(name="Reading"))
        assert result.success is True
        assert result.message == "Folder created"
        assert result.details == {}

    anyio.run(scenario)


def test_nested_sensitive_text_metadata_is_removed(monkeypatch: pytest.MonkeyPatch) -> None:
    client, _, session, _ = make_client(monkeypatch)
    session.call_result = SimpleNamespace(
        content=[SimpleNamespace(type="text", text="result")],
        isError=False,
        structuredContent={"requestId": {"apiKey": "axv-private", "id": "request-1"}},
    )

    async def scenario() -> None:
        async with client:
            await client.initialize()
            result = await client.discover_papers(
                DiscoverPapersArguments(keywords=("topic",), question="Question", difficulty=1)
            )
        assert "axv-private" not in result.model_dump_json()
        assert result.metadata == {"requestId": {"id": "request-1"}}

    anyio.run(scenario)


def test_nested_sensitive_mutation_details_are_removed(monkeypatch: pytest.MonkeyPatch) -> None:
    client, _, session, _ = make_client(monkeypatch)
    session.results_by_tool["create_folder"] = SimpleNamespace(
        content=[],
        isError=False,
        structuredContent={"count": 1, "data": {"apiKey": "axv-private", "folder_id": "folder-1"}},
    )

    async def scenario() -> None:
        async with client:
            await client.initialize()
            result = await client.create_folder(CreateFolderArguments(name="Reading"))
        assert "axv-private" not in result.model_dump_json()
        assert result.details == {"count": 1, "data": {"folder_id": "folder-1"}}

    anyio.run(scenario)


def test_tool_calls_require_successful_initialize(monkeypatch: pytest.MonkeyPatch) -> None:
    client, _, session, _ = make_client(monkeypatch)

    async def scenario() -> None:
        async with client:
            with pytest.raises(RuntimeError, match="initialize"):
                await client.list_tools()
        assert session.initialize_calls == 0

    anyio.run(scenario)


def test_client_cannot_be_used_outside_managed_session_or_reused(monkeypatch: pytest.MonkeyPatch) -> None:
    client, _, _, _ = make_client(monkeypatch)

    async def scenario() -> None:
        with pytest.raises(RuntimeError, match="managed session"):
            await client.list_tools()
        async with client:
            await client.initialize()
        with pytest.raises(RuntimeError, match="cannot be reused"):
            async with client:
                pass

    anyio.run(scenario)
