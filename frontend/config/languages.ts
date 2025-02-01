export interface Accent {
  code: string;
  name: string;
  voiceName: string; // Azure voice name
}

export interface Language {
  code: string;
  name: string;
  accents: Accent[];
}

export const languages: Language[] = [
  {
    code: "en",
    name: "English",
    accents: [
      {
        code: "us",
        name: "American",
        voiceName: "en-US-JennyNeural"
      },
      {
        code: "gb",
        name: "British",
        voiceName: "en-GB-SoniaNeural"
      },
      {
        code: "au",
        name: "Australian",
        voiceName: "en-AU-NatashaNeural"
      }
    ]
  },
  {
    code: "fr",
    name: "Français",
    accents: [
      {
        code: "fr",
        name: "France",
        voiceName: "fr-FR-DeniseNeural"
      },
      {
        code: "ca",
        name: "Canada",
        voiceName: "fr-CA-SylvieNeural"
      }
    ]
  },
  {
    code: "es",
    name: "Español",
    accents: [
      {
        code: "es",
        name: "España",
        voiceName: "es-ES-ElviraNeural"
      },
      {
        code: "mx",
        name: "México",
        voiceName: "es-MX-DaliaNeural"
      },
      {
        code: "ar",
        name: "Argentina",
        voiceName: "es-AR-ElenaNeural"
      }
    ]
  }
];
