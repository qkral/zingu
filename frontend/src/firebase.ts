import { initializeApp } from 'firebase/app';
import { 
  getFirestore, 
  collection, 
  query, 
  where, 
  getDocs, 
  doc, 
  setDoc,
  getDoc,
  Firestore,
  deleteDoc,
  connectFirestoreEmulator,
  enableNetwork,
  disableNetwork
} from 'firebase/firestore';
import { 
  getAuth, 
  onAuthStateChanged, 
  signOut,
  Auth
} from 'firebase/auth';

// Comprehensive Firebase configuration validation
const validateFirebaseConfig = () => {
  console.group(' Firebase Configuration Validation');
  /*console.log('Environment:', import.meta.env.MODE);*/
  
  const requiredEnvVars = [
    'VITE_FIREBASE_API_KEY',
    'VITE_FIREBASE_AUTH_DOMAIN',
    'VITE_FIREBASE_PROJECT_ID',
    'VITE_FIREBASE_STORAGE_BUCKET',
    'VITE_FIREBASE_MESSAGING_SENDER_ID',
    'VITE_FIREBASE_APP_ID'
  ];

  const missingVars: string[] = [];
  const configDetails: Record<string, string> = {};

  requiredEnvVars.forEach(key => {
    const value = import.meta.env[key];
    if (!value) {
      missingVars.push(key);
      console.error(` Missing environment variable: ${key}`);
    } else {
      configDetails[key] = value;
    }
  });

  if (missingVars.length > 0) {
    console.error('Missing Firebase configuration keys:', missingVars);
    console.groupEnd();
    throw new Error(`Invalid Firebase configuration: Missing ${missingVars.join(', ')}`);
  }

  console.groupEnd();

  return {
    apiKey: configDetails['VITE_FIREBASE_API_KEY'],
    authDomain: configDetails['VITE_FIREBASE_AUTH_DOMAIN'],
    projectId: configDetails['VITE_FIREBASE_PROJECT_ID'],
    storageBucket: configDetails['VITE_FIREBASE_STORAGE_BUCKET'],
    messagingSenderId: configDetails['VITE_FIREBASE_MESSAGING_SENDER_ID'],
    appId: configDetails['VITE_FIREBASE_APP_ID']
  };
};

// Construct Firebase configuration from environment variables
const firebaseConfig = validateFirebaseConfig();

// Main app initialization
let app, db, auth: Auth;

try {
  app = initializeApp(firebaseConfig);
  db = getFirestore(app);
  auth = getAuth(app);

  // Optional: Enable network if it was previously disabled
  try {
    enableNetwork(db);
  } catch (networkError) {
    console.warn('Could not enable Firestore network:', networkError);
  }

  // ONLY connect to emulator in explicit development mode
  if (import.meta.env.DEV && import.meta.env.VITE_USE_FIRESTORE_EMULATOR === 'true') {
    try {
      connectFirestoreEmulator(db, 'localhost', 8080);
      console.log('Connected to Firestore emulator');
    } catch (emulatorError) {
      console.warn('Could not connect to Firestore emulator:', emulatorError);
    }
  }
} catch (initError) {
  console.error(' Firebase Initialization Error:', initError);
  
  // Attempt to disable network to prevent further connection issues
  if (db) {
    try {
      disableNetwork(db);
    } catch (disableError) {
      console.error('Could not disable Firestore network:', disableError);
    }
  }
  
  throw initError;
}

// Separate Firebase app for conversation authentication
let conversationApp: any, conversationDb: Firestore | null = null;

// Synchronous initialization function
function initializeConversationFirestore() {
  try {
    conversationApp = initializeApp(firebaseConfig, 'ConversationApp');
    conversationDb = getFirestore(conversationApp);

    // Optional: Enable network if it was previously disabled
    if (import.meta.env.DEV) {
      try {
        enableNetwork(conversationDb).catch(networkError => {
          console.warn('Could not enable Conversation Firestore network:', networkError);
        });

        // ONLY connect to emulator in explicit development mode
        if (import.meta.env.VITE_USE_FIRESTORE_EMULATOR === 'true') {
          connectFirestoreEmulator(conversationDb, 'localhost', 8080);
          console.log('Connected to Conversation Firestore emulator');
        }
      } catch (emulatorError) {
        console.warn('Could not connect to Conversation Firestore emulator:', emulatorError);
      }
    }
  } catch (initError) {
    console.error('Conversation Firebase Initialization Error:', initError);
    
    // Safely check if conversationDb is not null before disabling network
    if (conversationDb !== null) {
      try {
        disableNetwork(conversationDb).catch(disableError => {
          console.error('Could not disable Conversation Firestore network:', disableError);
        });
      } catch (error) {
        console.error('Error attempting to disable network:', error);
      }
    }
  }
}

// Call initialization function
initializeConversationFirestore();

// Lazy authentication with explicit control
export const ensureAuth = async (requireAuth = false): Promise<string | null> => {
  return new Promise((resolve, reject) => {
    // Check if a user is already signed in
    const currentUser = auth.currentUser;

    // If a user is signed in, return their token
    if (currentUser) {
      currentUser.getIdToken()
        .then(token => resolve(token))
        .catch(error => {
          console.error('Error getting ID token:', error);
          resolve(null);
        });
      return;
    }

    // If authentication is not required, resolve with null
    if (!requireAuth) {
      resolve(null);
      return;
    }

    // If no user is signed in and auth is required, set up a listener
    const unsubscribe = onAuthStateChanged(
      auth, 
      async (user) => {
        // Unsubscribe to prevent memory leaks
        unsubscribe();

        if (user) {
          try {
            const token = await user.getIdToken();
            resolve(token);
          } catch (error) {
            console.error('Error getting ID token:', error);
            reject(new Error('Failed to get authentication token'));
          }
        } else {
          reject(new Error('No authenticated user found'));
        }
      },
      (error) => {
        // Unsubscribe to prevent memory leaks
        unsubscribe();
        console.error('Authentication state change error:', error);
        reject(error);
      }
    );

    // Set a timeout to prevent hanging
    setTimeout(() => {
      unsubscribe();
      reject(new Error('Authentication timeout'));
    }, 10000); // 10 seconds timeout
  });
};

// Method to explicitly sign out
export const signOutUser = async () => {
  try {
    await signOut(auth);
    console.log(' User signed out successfully');
  } catch (error) {
    console.error(' Sign out error:', error);
  }
};

// Utility function to sanitize messages for Firestore
const sanitizeMessageForFirestore = (message: any) => {
  // Create a new object with only allowed fields
  const sanitizedMessage: any = {
    text: message.text || '',
    role: message.role || 'unknown',
    timestamp: message.timestamp || new Date().toISOString()
  };

  // Optional fields that can be safely added if they exist
  if (message.topicName) sanitizedMessage.topicName = message.topicName;
  
  // Remove any Blob or complex objects
  delete sanitizedMessage.audioBlob;
  delete sanitizedMessage.pronunciationFeedback;
  delete sanitizedMessage.grammarCorrection;
  delete sanitizedMessage.grammarExplanation;
  delete sanitizedMessage.intonation;
  delete sanitizedMessage.pronunciationGuidance;

  return sanitizedMessage;
};

// Utility function to generate a consistent conversation ID
const generateConversationId = (userId: string, topicName?: string): string => {
  // Use a combination of user ID and topic name (or a default)
  const baseId = topicName 
    ? `${userId}_${topicName.toLowerCase().replace(/\s+/g, '_')}`
    : `${userId}_default_conversation`;
  
  // Create a consistent hash to ensure uniqueness
  const hash = (str: string) => {
    let hash = 0;
    for (let i = 0; i < str.length; i++) {
      const char = str.charCodeAt(i);
      hash = ((hash << 5) - hash) + char;
      hash = hash & hash; // Convert to 32-bit integer
    }
    return Math.abs(hash).toString(36);
  };

  return `${baseId}_${hash(baseId)}`;
};

// Utility function to get or create an anonymous user ID
const getAnonymousUserId = (): string => {
  // Check if anonymous user ID exists in local storage
  const storedAnonymousId = localStorage.getItem('anonymousUserId');
  if (storedAnonymousId) {
    return storedAnonymousId;
  }

  // Generate a new anonymous user ID
  const newAnonymousId = `anonymous_${Date.now()}_${Math.random().toString(36).substring(2, 15)}`;
  
  // Store in local storage for persistence across page reloads
  localStorage.setItem('anonymousUserId', newAnonymousId);
  
  return newAnonymousId;
};

// Function to save conversation
export const saveConversation = async (
  messages: any[], 
  topicName?: string,
  isKidsMode?: boolean,
  selectedVoiceGender?: 'male' | 'female' | 'kid',
  selectedAccent?: string
): Promise<string> => {
  try {
    // Ensure conversationDb is not null before using it
    if (!conversationDb) {
      throw new Error('Conversation database not initialized');
    }

    // Determine user ID (authenticated or anonymous)
    let userId: string;
    let userEmail: string | null = null;
    let isAnonymous = false;

    // Check for authenticated user first
    const conversationUser = auth.currentUser;
    if (conversationUser) {
      userId = conversationUser.uid;
      userEmail = conversationUser.email;
    } else {
      // If no authenticated user, use anonymous user ID
      userId = getAnonymousUserId();
      isAnonymous = true;
    }

    // Validate user ID
    if (!userId) {
      throw new Error('Unable to determine user identity');
    }

    // Validate voice gender
    const validVoiceGenders = ['male', 'female', 'kid'];
    const safeVoiceGender = validVoiceGenders.includes(selectedVoiceGender || '') 
      ? selectedVoiceGender 
      : 'female';

    // Generate a consistent conversation ID
    const conversationId = generateConversationId(userId, topicName);

    // Sanitize messages
    const sanitizedMessages = messages.map(sanitizeMessageForFirestore);

    // Create a reference to the conversation document using the consistent ID
    const conversationRef = doc(conversationDb, 'aicoach_conversations', conversationId);

    // Prepare conversation data with explicit userId and userEmail
    const conversationData = {
      userId: userId,  // Explicitly set userId
      userEmail: userEmail,  // Add user email (null for anonymous)
      messages: sanitizedMessages,
      topicName: topicName || 'Unnamed Conversation',
      originalTimestamp: Date.now(),
      language: sanitizedMessages[0]?.language || 'en',
      accent: selectedAccent || sanitizedMessages[0]?.accent || 'neutral',
      isAnonymous: isAnonymous,
      
      // Add kids mode and voice gender information
      isKidsMode: isKidsMode || false,
      selectedVoiceGender: safeVoiceGender
    };

    try {
      // Overwrite the document with merged data
      await setDoc(conversationRef, conversationData, { merge: false });
      console.log('Conversation saved successfully', {
        conversationId,
        userId,
        userEmail,
        isAnonymous,
        messageCount: conversationData.messages.length,
        isKidsMode,
        selectedVoiceGender: conversationData.selectedVoiceGender,
        selectedAccent: conversationData.accent
      });
      
      return conversationId;
    } catch (writeError: unknown) {
      // Detailed error logging
      if (writeError instanceof Error) {
        console.error('Error saving conversation:', {
          message: writeError.message,
          name: writeError.name,
          stack: writeError.stack
        });
      } else {
        console.error('Unknown error saving conversation:', writeError);
      }
      throw writeError;
    }
  } catch (error) {
    // Detailed error logging
    if (error instanceof Error) {
      console.error('Conversation save preparation error:', {
        message: error.message,
        name: error.name,
        stack: error.stack
      });
    } else {
      console.error('Unknown conversation save preparation error:', error);
    }
    throw error;
  }
};

// Define an interface for conversation history
interface ConversationHistory {
  id: string;
  topicId?: string;
  timestamp?: number;
  topicName?: string;
  messages?: any[];
  originalTimestamp?: number;
}

// Function to retrieve conversation history
export const getConversationHistory = async (topicName?: string): Promise<ConversationHistory[]> => {
  try {
    // Ensure conversationDb is not null before using it
    if (!conversationDb) {
      console.error('Conversation database not initialized');
      return [];
    }

    // Determine user ID (authenticated or anonymous)
    let userId: string | null = null;
    let userEmail: string | null = null;
    let isAnonymous = false;

    // Check for authenticated user first
    const currentUser = auth.currentUser;
    if (currentUser) {
      userId = currentUser.uid;
      userEmail = currentUser.email;
    } else {
      // Try to get anonymous user ID from local storage
      const storedAnonymousId = localStorage.getItem('anonymousUserId');
      if (storedAnonymousId) {
        userId = storedAnonymousId;
        isAnonymous = true;
      }
    }

    // If no user ID found, return empty array
    if (!userId) {
      console.warn('No user identity found for conversation history');
      return [];
    }

    // Create a reference to the conversations collection
    const conversationsRef = collection(conversationDb, 'aicoach_conversations');

    // Prepare query
    const q = topicName 
      ? query(
          conversationsRef, 
          where('userId', '==', userId),
          where('topicName', '==', topicName)
        )
      : query(
          conversationsRef, 
          where('userId', '==', userId)
        );

    // Fetch conversations
    const querySnapshot = await getDocs(q);

    // Map and return conversations
    const conversations = querySnapshot.docs
      .map(doc => {
        const data = doc.data();
        return { 
          id: doc.id, 
          ...data,
          originalTimestamp: data.originalTimestamp || Date.now()
        } as ConversationHistory;
      })
      .sort((a, b) => (b.originalTimestamp || 0) - (a.originalTimestamp || 0));

    console.log('Conversation History Retrieved', {
      count: conversations.length,
      userId,
      userEmail,
      isAnonymous
    });

    return conversations;
  } catch (error: unknown) {
    // Detailed error logging
    if (error instanceof Error) {
      console.error('Error retrieving conversation history:', {
        errorName: error.name,
        errorMessage: error.message,
        errorStack: error.stack
      });
    } else {
      console.error('Unknown error retrieving conversation history:', error);
    }
    return [];
  }
};

// Function to load a specific conversation by its ID
export const loadConversation = async (conversationId: string): Promise<any | null> => {
  try {
    // Ensure conversationDb is not null before using it
    if (!conversationDb) {
      console.error('Conversation database not initialized');
      return null;
    }

    // Determine user ID (authenticated or anonymous)
    let userId: string | null = null;
    let userEmail: string | null = null;
    let isAnonymous = false;

    // Check for authenticated user first
    const currentUser = auth.currentUser;
    if (currentUser) {
      userId = currentUser.uid;
      userEmail = currentUser.email;
    } else {
      // Try to get anonymous user ID from local storage
      const storedAnonymousId = localStorage.getItem('anonymousUserId');
      if (storedAnonymousId) {
        userId = storedAnonymousId;
        isAnonymous = true;
      }
    }

    // If no user ID found, return null
    if (!userId) {
      console.warn('No user identity found for loading conversation');
      return null;
    }

    // Create a reference to the specific conversation document
    const conversationRef = doc(conversationDb, 'aicoach_conversations', conversationId);

    // Fetch the document
    const docSnap = await getDoc(conversationRef);

    // Check if document exists
    if (docSnap.exists()) {
      const conversationData = docSnap.data();
      
      // Verify the conversation belongs to the current user
      if (conversationData?.userId !== userId) {
        console.error('Unauthorized access to conversation', {
          requestedUserId: userId,
          requestedUserEmail: userEmail,
          conversationUserId: conversationData?.userId,
          conversationUserEmail: conversationData?.userEmail,
          isAnonymous
        });
        return null;
      }

      return {
        id: docSnap.id,
        ...conversationData,
        messages: conversationData?.messages || [],
        originalTimestamp: conversationData?.originalTimestamp
      };
    } else {
      console.error('No such conversation found');
      return null;
    }
  } catch (error: unknown) {
    // Detailed error logging
    if (error instanceof Error) {
      console.error('Error loading conversation:', {
        errorName: error.name,
        errorMessage: error.message,
        errorStack: error.stack
      });
    } else {
      console.error('Unknown error loading conversation:', error);
    }
    return null;
  }
};

// Function to delete a conversation
export const deleteConversation = async (conversationId: string): Promise<boolean> => {
  try {
    // Ensure conversationDb is not null before using it
    if (!conversationDb) {
      console.error('Conversation database not initialized');
      return false;
    }

    // Determine user ID (authenticated or anonymous)
    let userId: string | null = null;
    let userEmail: string | null = null;
    let isAnonymous = false;

    // Check for authenticated user first
    const currentUser = auth.currentUser;
    if (currentUser) {
      userId = currentUser.uid;
      userEmail = currentUser.email;
    } else {
      // Try to get anonymous user ID from local storage
      const storedAnonymousId = localStorage.getItem('anonymousUserId');
      if (storedAnonymousId) {
        userId = storedAnonymousId;
        isAnonymous = true;
      }
    }

    // If no user ID found, return false
    if (!userId) {
      console.warn('No user identity found for deleting conversation');
      return false;
    }

    // Create a reference to the specific conversation document
    const conversationRef = doc(conversationDb, 'aicoach_conversations', conversationId);

    // Verify the conversation belongs to the current user
    const docSnap = await getDoc(conversationRef);
    if (!docSnap.exists() || docSnap.data()?.userId !== userId) {
      console.error('Unauthorized deletion attempt', {
        requestedUserId: userId,
        requestedUserEmail: userEmail,
        conversationUserId: docSnap.data()?.userId,
        conversationUserEmail: docSnap.data()?.userEmail,
        isAnonymous
      });
      return false;
    }

    // Delete the conversation
    await deleteDoc(conversationRef);

    console.log('Conversation deleted successfully', {
      conversationId,
      userId,
      userEmail,
      isAnonymous
    });
    return true;
  } catch (error: unknown) {
    // Detailed error logging
    if (error instanceof Error) {
      console.error('Error deleting conversation:', {
        errorName: error.name,
        errorMessage: error.message,
        errorStack: error.stack
      });
    } else {
      console.error('Unknown error deleting conversation:', error);
    }
    return false;
  }
};

// Export the main app's auth and db
export { db, auth };
