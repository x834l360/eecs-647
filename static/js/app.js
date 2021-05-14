async function register(user) {
    const resp = await fetch("/api/register", {
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify(user),
    })
}


async function login(username, password) {
    const resp = await fetch("/api/login", {
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({username, password}),
    })
}
