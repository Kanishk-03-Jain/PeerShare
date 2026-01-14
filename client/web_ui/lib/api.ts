export async function apiRequest(path: string, options?: RequestInit) {
    const defaults = {
        headers: {
            "Content-Type": "application/json",
        },
    };

    // merge default with custom
    const config = {
        ...defaults,
        ...options,
        headers: {
            ...defaults.headers,
            ...options?.headers
        }
    };

    const response = await fetch(path, config)

    if (!response.ok) {
        const errorBody = await response.json().catch(() => ({}));
        // FastAPI validation error
        console.log("errorBody: ", errorBody)
        if (Array.isArray(errorBody.detail.detail)) {
            throw {
                type: "validation",
                errors: errorBody.detail.detail,
            };

        }
        throw {
            type: "generic",
            message: errorBody.detail || "Something went wrong",
        };
    }

    return response.json();
}