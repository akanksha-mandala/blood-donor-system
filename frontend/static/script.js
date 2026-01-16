const BASE_URL = "http://127.0.0.1:5000"; // Flask backend

// Helper: get lat/lon from city using OpenStreetMap
async function getCoordinates(city) {
    const res = await fetch(`https://nominatim.openstreetmap.org/search?format=json&q=${city}`);
    const data = await res.json();
    if (!data.length) throw new Error("City not found!");
    return { latitude: parseFloat(data[0].lat), longitude: parseFloat(data[0].lon) };
}

// ✅ Register Donor
async function handleDonorRegistration() {
    console.log("🔎 handleDonorRegistration called");

    const city = document.getElementById("city").value;
    let coords = { latitude: null, longitude: null };
    try { 
        coords = await getCoordinates(city); 
    } catch(e) { 
        alert(e.message || e); 
        return; 
    }

    const data = {
        full_name: document.getElementById("name").value,
        age: document.getElementById("age").value,
        email: document.getElementById("email").value,
        phone: document.getElementById("phone").value,
        blood_group: document.getElementById("bloodGroup").value,
        city: city,
        latitude: coords.latitude,
        longitude: coords.longitude
    };

    console.log("🩸 Sending donor data to backend:", data);

    if (!data.full_name || !data.age || !data.email || !data.phone || !data.blood_group || !data.city) {
        alert("⚠️ Please fill all fields!");
        return;
    }

    try {
        const res = await fetch(`${BASE_URL}/api/donors/register`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(data)
        });

        console.log("📬 fetch returned status:", res.status);
        let result;
        try {
            result = await res.json();
            console.log("📨 backend response JSON:", result);
        } catch (e) {
            console.error("⚠️ failed to parse JSON response", e);
            alert("Server returned invalid JSON");
            return;
        }

        alert(result.message || "Donor registered successfully!");

        // ✅ After registering, load nearby requests
        const requestsRes = await fetch(`${BASE_URL}/api/requests`);
        const requests = await requestsRes.json();

        const requestsFeed = document.getElementById("requests-feed");
        if (!requestsFeed) return; // safety check

        if (requests.length === 0) {
            requestsFeed.innerHTML = '<p class="text-gray-500 italic">No requests nearby...</p>';
        } else {
            requestsFeed.innerHTML = requests.map(r => `
                <div class="p-4 bg-white rounded-lg shadow-md border">
                    <p><strong>${r.full_name}</strong> needs <strong>${r.blood_group_needed}</strong> blood at <strong>${r.hospital_name}</strong></p>
                    <p class="text-sm text-gray-500">City: ${r.city}</p>
                </div>
            `).join('');
        }

    } catch(err) {
        console.error("❌ Error during donor registration:", err);
        alert("❌ Failed to register donor. Check console for details.");
    }
}

// ✅ Register Recipient
async function handleRecipientRegistration() {
    const city = document.getElementById("recipient_city").value;
    let coords = { latitude: null, longitude: null };
    try { coords = await getCoordinates(city); } catch(e){ alert(e); return; }

    const data = {
        full_name: document.getElementById("recipient_name").value,
        phone: document.getElementById("recipient_phone").value,
        email: document.getElementById("recipient_email").value,
        blood_group_needed: document.getElementById("recipient_blood").value,
        city: city,
        latitude: coords.latitude,
        longitude: coords.longitude
    };

    const res = await fetch(`${BASE_URL}/api/recipients/register`, {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify(data)
    });

    const result = await res.json();
    alert(result.message);
}

// ✅ Search Donors
async function searchDonors() {
    const city = document.getElementById("search_city").value;
    let coords = { latitude: null, longitude: null };
    try { coords = await getCoordinates(city); } catch(e){ alert(e); return; }

    const data = {
        blood_group: document.getElementById("search_blood").value,
        latitude: coords.latitude,
        longitude: coords.longitude
    };

    const res = await fetch(`${BASE_URL}/search/donor`, {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify(data)
    });

    const result = await res.json();
    const ul = document.getElementById("results");
    ul.innerHTML = "";

    result.matching_donors.forEach(d => {
        const li = document.createElement("li");
        li.textContent = `${d.full_name} | ${d.blood_group} | ${d.city} | ${d.phone}`;
        ul.appendChild(li);
    });
}

console.log("✅ script.js loaded successfully");

// 👇 make functions accessible to HTML onclick
window.handleDonorRegistration = handleDonorRegistration;
window.handleRecipientRegistration = handleRecipientRegistration;
window.searchDonors = searchDonors;
