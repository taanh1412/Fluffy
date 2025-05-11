console.log("main.js loaded successfully");

if (typeof React === "undefined" || typeof ReactDOM === "undefined") {
    console.error("React or ReactDOM failed to load. Check network requests for CDN scripts.");
} else {
    const { useReducer, useEffect } = React;
    const { createRoot } = ReactDOM;

    const initialState = {
        userId: "",
        password: "",
        file: null,
        fileHash: "",
        searchQuery: "",
        searchResults: [],
        fileList: [],
        isLoggedIn: !!localStorage.getItem("authToken"),
        token: localStorage.getItem("authToken") || "",
        error: ""
    };

    const reducer = (state, action) => {
        switch (action.type) {
            case "SET_USERID":
                return { ...state, userId: action.payload };
            case "SET_PASSWORD":
                return { ...state, password: action.payload };
            case "SET_FILE":
                return { ...state, file: action.payload };
            case "SET_FILE_HASH":
                return { ...state, fileHash: action.payload };
            case "SET_SEARCH_QUERY":
                return { ...state, searchQuery: action.payload };
            case "SET_SEARCH_RESULTS":
                return { ...state, searchResults: action.payload };
            case "SET_FILE_LIST":
                return { ...state, fileList: action.payload };
            case "LOGIN":
                return { ...state, isLoggedIn: true, token: action.payload, error: "", userId: action.userId };
            case "LOGOUT":
                localStorage.removeItem("authToken");
                return { ...state, isLoggedIn: false, token: "", userId: "", password: "", file: null, fileHash: "", searchQuery: "", searchResults: [], fileList: [], error: "" };
            case "SET_ERROR":
                return { ...state, error: action.payload };
            default:
                return state;
        }
    };

    const App = () => {
        const [state, dispatch] = useReducer(reducer, initialState);

        const apiCall = async (url, method, data = null) => {
            try {
                const headers = {
                    "X-Auth-Token": state.token
                };
                if (method === "POST" && typeof data === "string") {
                    headers["Content-Type"] = "application/json";
                }
                const response = await fetch(`http://localhost:5001${url}`, {  // Changed to 5001
                    method,
                    headers,
                    body: data,
                });
                if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);
                return await response.json();
            } catch (err) {
                console.error("API Error:", err.message);
                dispatch({ type: "SET_ERROR", payload: err.message });
                return null;
            }
        };

        const handleRegister = async () => {
            if (!state.userId || !state.password) {
                dispatch({ type: "SET_ERROR", payload: "Username and password required." });
                return;
            }
            const result = await apiCall("/api/register", "POST", JSON.stringify({ username: state.userId, password: state.password }));
            if (result?.token) {
                localStorage.setItem("authToken", result.token);
                dispatch({ type: "LOGIN", payload: result.token, userId: state.userId });
            }
        };

        const handleLogin = async () => {
            if (!state.userId || !state.password) {
                dispatch({ type: "SET_ERROR", payload: "Username and password required." });
                return;
            }
            const result = await apiCall("/api/login", "POST", JSON.stringify({ username: state.userId, password: state.password }));
            if (result?.token) {
                localStorage.setItem("authToken", result.token);
                dispatch({ type: "LOGIN", payload: result.token, userId: state.userId });
            }
        };

        const handleLogout = () => {
            dispatch({ type: "LOGOUT" });
        };

        const handleUpload = async () => {
            if (!state.file) {
                dispatch({ type: "SET_ERROR", payload: "Please select a file." });
                return;
            }
            const formData = new FormData();
            formData.append("file", state.file);
            formData.append("token", state.token);
            const result = await apiCall("/api/upload", "POST", formData);
            if (result?.file_hash) {
                dispatch({ type: "SET_FILE_HASH", payload: result.file_hash });
                dispatch({ type: "SET_ERROR", payload: "" });
            }
        };

        const handleDownload = async () => {
            if (!state.fileHash) {
                dispatch({ type: "SET_ERROR", payload: "Please provide a File Hash." });
                return;
            }
            const result = await apiCall(`/api/download/${state.fileHash}`, "GET");
            if (result?.data) {
                alert(`Downloaded: ${result.data}`);
                dispatch({ type: "SET_ERROR", payload: "" });
            }
        };

        const handleSearch = async () => {
            if (!state.searchQuery) {
                dispatch({ type: "SET_ERROR", payload: "Please enter a search query." });
                return;
            }
            const result = await apiCall(`/api/search?query=${state.searchQuery}`, "GET");
            if (result) {
                dispatch({ type: "SET_SEARCH_RESULTS", payload: result });
                dispatch({ type: "SET_ERROR", payload: "" });
            }
        };

        const handleList = async () => {
            const result = await apiCall("/api/list", "GET");
            if (result) {
                dispatch({ type: "SET_FILE_LIST", payload: result });
                dispatch({ type: "SET_ERROR", payload: "" });
            }
        };

        const handleDelete = async () => {
            if (!state.fileHash) {
                dispatch({ type: "SET_ERROR", payload: "Please provide a File Hash." });
                return;
            }
            const result = await apiCall(`/api/delete/${state.fileHash}`, "DELETE");
            if (result?.success) {
                dispatch({ type: "SET_FILE_HASH", payload: "" });
                dispatch({ type: "SET_ERROR", payload: "" });
                handleList(); // Refresh the file list
            }
        };

        const handleUpdate = async () => {
            if (!state.fileHash || !state.file) {
                dispatch({ type: "SET_ERROR", payload: "Please provide a File Hash and select a new file." });
                return;
            }
            const formData = new FormData();
            formData.append("file", state.file);
            formData.append("token", state.token);
            const result = await apiCall(`/api/update/${state.fileHash}`, "PUT", formData);
            if (result?.success) {
                dispatch({ type: "SET_FILE_HASH", payload: "" });
                dispatch({ type: "SET_ERROR", payload: "" });
                handleList(); // Refresh the file list
            }
        };

        if (!state.isLoggedIn) {
            return React.createElement("div", { className: "app" },
                React.createElement("h1", null, "File Storage App"),
                state.error && React.createElement("p", { className: "error" }, state.error),
                React.createElement("input", {
                    type: "text",
                    placeholder: "Username",
                    value: state.userId,
                    onChange: (e) => dispatch({ type: "SET_USERID", payload: e.target.value })
                }),
                React.createElement("input", {
                    type: "password",
                    placeholder: "Password",
                    value: state.password,
                    onChange: (e) => dispatch({ type: "SET_PASSWORD", payload: e.target.value })
                }),
                React.createElement("button", { onClick: handleRegister }, "Register"),
                React.createElement("button", { onClick: handleLogin }, "Login")
            );
        }

        return React.createElement("div", { className: "app" },
            React.createElement("h1", null, "File Storage App"),
            state.error && React.createElement("p", { className: "error" }, state.error),
            React.createElement("button", { onClick: handleLogout }, "Logout"),
            React.createElement("p", null, `Welcome, ${state.userId}!`),
            React.createElement("input", {
                type: "file",
                onChange: (e) => dispatch({ type: "SET_FILE", payload: e.target.files[0] })
            }),
            React.createElement("button", { onClick: handleUpload }, "Upload"),
            React.createElement("input", {
                type: "text",
                placeholder: "File Hash",
                value: state.fileHash,
                onChange: (e) => dispatch({ type: "SET_FILE_HASH", payload: e.target.value })
            }),
            React.createElement("button", { onClick: handleDownload }, "Download"),
            React.createElement("button", { onClick: handleDelete }, "Delete"),
            React.createElement("button", { onClick: handleUpdate }, "Update"),
            React.createElement("input", {
                type: "text",
                placeholder: "Search Query",
                value: state.searchQuery,
                onChange: (e) => dispatch({ type: "SET_SEARCH_QUERY", payload: e.target.value })
            }),
            React.createElement("button", { onClick: handleSearch }, "Search"),
            React.createElement("button", { onClick: handleList }, "List Files"),
            React.createElement("div", { id: "searchResults" },
                React.createElement("h3", null, "Search Results"),
                React.createElement("ul", null,
                    state.searchResults.map((result, index) =>
                        React.createElement("li", { key: index }, `${result.file_name} (${result.file_hash})`)
                    )
                )
            ),
            React.createElement("div", { id: "fileList" },
                React.createElement("h3", null, "Your Files"),
                React.createElement("ul", null,
                    state.fileList.map((file, index) =>
                        React.createElement("li", { key: index }, `${file.file_name} (${file.file_hash})`)
                    )
                )
            )
        );
    };

    const root = createRoot(document.getElementById("app"));
    root.render(React.createElement(App));
}