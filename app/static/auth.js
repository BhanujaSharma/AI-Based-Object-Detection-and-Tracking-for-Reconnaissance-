document.addEventListener("DOMContentLoaded", async () => {
    const loginBtn = document.getElementById("loginBtn");

    loginBtn.onclick = async () => {
        const authClient = await window.AuthClient.create();

        await authClient.login({
            identityProvider: "https://identity.ic0.app/#authorize",
            onSuccess: async () => {
                const identity = authClient.getIdentity();
                const principal = identity.getPrincipal().toText();

                const response = await fetch("/auth/callback", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ principal }),
                });

                if (response.redirected) {
                    window.location.href = response.url;
                }
            }
        });
    };
});
