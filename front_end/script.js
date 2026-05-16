const API_BASE_URL = "https://jtevt1xgeg.execute-api.us-east-1.amazonaws.com/dev";


// ======================================================
// LOGIN FUNCTION
// ======================================================

async function loginUser() {

    const email = document.getElementById("email").value;
    const password = document.getElementById("password").value;

    if (email === "" || password === "") {
        document.getElementById("message").innerText =
            "Please enter email and password";
        return;
    }

    try {
        const response = await fetch(`${API_BASE_URL}/login`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                email: email,
                password: password
            })
        });

        const data = await response.json();

        if (data.success === true) {
            localStorage.setItem("userEmail", email);
            localStorage.setItem("userName", data.user_name);
            window.location.href = "main.html";
        } else {
            document.getElementById("message").innerText =
                "email or password is invalid";
        }

    } catch (error) {
        document.getElementById("message").innerText =
            "Backend connection failed";
    }
}


// ======================================================
// REGISTER FUNCTION
// ======================================================

async function registerUser() {

    const email = document.getElementById("registerEmail").value;
    const username = document.getElementById("registerUsername").value;
    const password = document.getElementById("registerPassword").value;

    if (email === "" || username === "" || password === "") {
        document.getElementById("registerMessage").style.color = "red";
        document.getElementById("registerMessage").innerText =
            "Please fill all fields";
        return;
    }

    try {
        const response = await fetch(`${API_BASE_URL}/register`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                email: email,
                user_name: username,
                password: password
            })
        });

        const data = await response.json();

        if (data.success === true) {
            document.getElementById("registerMessage").style.color = "green";
            document.getElementById("registerMessage").innerText =
                "Registration successful";

            setTimeout(() => {
                window.location.href = "login.html";
            }, 1500);

        } else {
            document.getElementById("registerMessage").style.color = "red";
            document.getElementById("registerMessage").innerText =
                data.message;
        }

    } catch (error) {
        document.getElementById("registerMessage").style.color = "red";
        document.getElementById("registerMessage").innerText =
            "Backend connection failed";
    }
}


// ======================================================
// LOAD USERNAME ON MAIN PAGE
// ======================================================

window.onload = function () {

    const usernameElement = document.getElementById("username");

    if (usernameElement) {

        const userEmail = localStorage.getItem("userEmail");
        const userName = localStorage.getItem("userName");

        if (!userEmail) {
            window.location.href = "login.html";
            return;
        }

        usernameElement.innerText = userName;

        loadSubscriptions();
    }
};


// ======================================================
// LOGOUT
// ======================================================

function logoutUser() {
    localStorage.clear();
    window.location.href = "login.html";
}


// ======================================================
// SUBSCRIBE MUSIC
// ======================================================

async function subscribeMusic(song) {

    const email = localStorage.getItem("userEmail");

    if (!email) {
        alert("Please login again");
        window.location.href = "login.html";
        return;
    }

    try {
        const response = await fetch(`${API_BASE_URL}/subscribe`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                email: email,
                title: song.title,
                artist: song.artist,
                album: song.album,
                year: song.year,
                image_url: song.image_url
            })
        });

        const data = await response.json();

        console.log(data.message);

        if (data.success === true) {
            loadSubscriptions();
        } else {
            alert(data.message);
        }

    } catch (error) {
        alert("Backend connection failed");
    }
}


// ======================================================
// LOAD USER SUBSCRIPTIONS
// ======================================================

async function loadSubscriptions() {

    const email = localStorage.getItem("userEmail");

    if (!email) {
        return;
    }

    try {
        const response = await fetch(
            `${API_BASE_URL}/subscriptions?email=${encodeURIComponent(email)}`
        );

        const data = await response.json();

        const resultsDiv = document.getElementById("subscriptionResults");

        if (!resultsDiv) {
            return;
        }

        resultsDiv.innerHTML = "";

        if (!data.subscriptions || data.subscriptions.length === 0) {
            resultsDiv.innerHTML = "<p>No subscriptions found.</p>";
            return;
        }

        data.subscriptions.forEach(function (song) {

            const songCard = document.createElement("div");
            songCard.className = "song-card";

            songCard.innerHTML = `

                <img src="${song.image_display_url}" onerror="this.src='https://via.placeholder.com/120'">

                <div>
                    <h3>${song.title}</h3>

                    <p>Artist: ${song.artist}</p>

                    <p>Album: ${song.album}</p>

                    <p>Year: ${song.year}</p>

                    <button onclick='removeSubscription("${song.music_id}")'>
                        Remove
                    </button>
                </div>
            `;

            resultsDiv.appendChild(songCard);
        });

    } catch (error) {
        console.log("Unable to load subscriptions");
    }
}


// ======================================================
// SEARCH MUSIC
// ======================================================

async function searchMusic() {

    const title = document.getElementById("title").value;
    const artist = document.getElementById("artist").value;
    const album = document.getElementById("album").value;
    const year = document.getElementById("year").value;

    if (
        title === "" &&
        artist === "" &&
        album === "" &&
        year === ""
    ) {
        document.getElementById("searchMessage").innerText =
            "Please enter at least one search field";
        return;
    }

    document.getElementById("searchMessage").innerText = "";

    const queryParams = new URLSearchParams();

    if (title !== "") {
        queryParams.append("title", title);
    }

    if (artist !== "") {
        queryParams.append("artist", artist);
    }

    if (album !== "") {
        queryParams.append("album", album);
    }

    if (year !== "") {
        queryParams.append("year", year);
    }

    try {
        const response = await fetch(
            `${API_BASE_URL}/music/search?${queryParams.toString()}`
        );

        const data = await response.json();

        const resultsDiv = document.getElementById("searchResults");
        resultsDiv.innerHTML = "";

        if (!data.songs || data.songs.length === 0) {
            document.getElementById("searchMessage").innerText =
                "No result is retrieved. Please query again";
            return;
        }

        data.songs.forEach(function (song) {

            const songCard = document.createElement("div");
            songCard.className = "song-card";

            songCard.innerHTML = `

                <img src="${song.image_display_url}" onerror="this.src='https://via.placeholder.com/120'">

                <div>
                    <h3>${song.title}</h3>
                    <p>Artist: ${song.artist}</p>
                    <p>Album: ${song.album}</p>
                    <p>Year: ${song.year}</p>

                    <button class="subscribe-btn" 
                            onclick='subscribeMusic(${JSON.stringify(song)})'>
                        Subscribe
                    </button>
                </div>
            `;

            resultsDiv.appendChild(songCard);
        });

    } catch (error) {
        document.getElementById("searchMessage").innerText =
            "Backend connection failed";
    }
}


// ======================================================
// REMOVE SUBSCRIPTION
// ======================================================

async function removeSubscription(music_id) {

    const email = localStorage.getItem("userEmail");

    if (!email) {
        alert("Please login again");
        window.location.href = "login.html";
        return;
    }

    try {
        const response = await fetch(`${API_BASE_URL}/remove_subscription`, {
            method: "DELETE",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                email: email,
                music_id: music_id
            })
        });

        const data = await response.json();

        console.log(data);

        if (data.success === true) {
            alert("Subscription removed successfully");
            loadSubscriptions();
        } else {
            alert(data.message || "Unable to remove subscription");
        }

    } catch (error) {
        console.error("Delete error:", error);
        alert("Backend connection failed");
    }
}