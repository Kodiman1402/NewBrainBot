// Wir warten, bis das HTML vollständig im Browser geladen ist
document.addEventListener("DOMContentLoaded", () => {
    
    // Wir suchen unser HTML-Element mit der ID "typewriter"
    const typewriterElement = document.getElementById("typewriter");
    
    // Wir lesen den Text aus dem data-text Attribut aus
    const textToType = typewriterElement.getAttribute("data-text");
    
    // Eine Variable, um mitzuzählen, beim wievielten Buchstaben wir sind
    let index = 0;

    // Wir stellen sicher, dass das Element leer ist, bevor wir anfangen
    typewriterElement.textContent = "";

    // Das ist die Funktion, die das Tippen simuliert
    function typeWriter() {
        // Solange noch Buchstaben übrig sind...
        if (index < textToType.length) {
            // ...fügen wir den nächsten Buchstaben zum Element hinzu
            typewriterElement.textContent += textToType.charAt(index);
            index++;
            
            // Hacker tippen nicht immer exakt gleich schnell. 
            // Wir erzeugen eine zufällige Pause zwischen 50 und 150 Millisekunden.
            const randomSpeed = Math.floor(Math.random() * 100) + 50;
            
            // Wir rufen die Funktion nach der Pause erneut auf
            setTimeout(typeWriter, randomSpeed);
        } else {
            // Wenn der Text fertig getippt ist, fügen wir die CSS-Klasse "cursor" hinzu,
            // damit der Unterstrich (_) anfängt zu blinken.
            typewriterElement.classList.add("cursor");
        }
    }

    // Wir starten den Effekt eine halbe Sekunde (500ms) nachdem die Seite geladen wurde
    setTimeout(typeWriter, 500);
});
