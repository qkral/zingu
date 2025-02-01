import { initializeApp } from 'firebase/app';
import { 
  getFirestore, 
  collection, 
  serverTimestamp, 
  query, 
  where, 
  getDocs, 
  doc, 
  setDoc,
  getDoc,
  Firestore,
  deleteDoc,
  orderBy,
  connectFirestoreEmulator,
  enableNetwork,
  disableNetwork
} from 'firebase/firestore';
import { 
  getAuth, 
  signInAnonymously, 
  onAuthStateChanged, 
  AuthError,
  User,
  getIdToken,
  signOut,
  Auth
} from 'firebase/auth';

// Comprehensive Firebase configuration validation
const validateFirebaseConfig = () => {
  console.group(' Firebase Configuration Validation');
  console.log('Environment:', import.meta.env.MODE);
  
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
      console.log(` ${key}: ${value}`);
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
let app, db, auth;

try {
  app = initializeApp(firebaseConfig);
  db = getFirestore(app);
  auth = getAuth(app);

  // Optional: Enable network if it was previously disabled
  try {
    await enableNetwork(db);
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
      await disableNetwork(db);
    } catch (disableError) {
      console.error('Could not disable Firestore network:', disableError);
    }
  }
  
  throw initError;
}

// Separate Firebase app for conversation authentication
let conversationApp: any, conversationDb: Firestore, conversationAuth: Auth;

try {
  conversationApp = initializeApp(firebaseConfig, 'ConversationApp');
  conversationDb = getFirestore(conversationApp);
  conversationAuth = getAuth(conversationApp);

  // Optional: Enable network if it was previously disabled
  try {
    await enableNetwork(conversationDb);
  } catch (networkError) {
    console.warn('Could not enable Conversation Firestore network:', networkError);
  }

  // ONLY connect to emulator in explicit development mode
  if (import.meta.env.DEV && import.meta.env.VITE_USE_FIRESTORE_EMULATOR === 'true') {
    try {
      connectFirestoreEmulator(conversationDb, 'localhost', 8080);
      console.log('Connected to Conversation Firestore emulator');
    } catch (emulatorError) {
      console.warn('Could not connect to Conversation Firestore emulator:', emulatorError);
    }
  }
} catch (initError) {
  console.error(' Conversation Firebase Initialization Error:', initError);
  
  // Attempt to disable network to prevent further connection issues
  if (conversationDb) {
    try {
      await disableNetwork(conversationDb);
    } catch (disableError) {
      console.error('Could not disable Conversation Firestore network:', disableError);
    }
  }
  
  throw initError;
}

// Utility to check if a user is anonymous
const isAnonymousUser = (user: User | null): boolean => {
  return user?.isAnonymous ?? false;
};

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

// Persistent storage for conversation authentication
let persistentConversationUser: User | null = null;

// Dedicated method for conversation-specific anonymous authentication
const getConversationAuthUser = async (): Promise<User | null> => {
  try {
    // If a persistent user exists, return it
    if (persistentConversationUser) {
      return persistentConversationUser;
    }

    // Create a new anonymous user specifically for conversation saving
    const userCredential = await signInAnonymously(conversationAuth);
    persistentConversationUser = userCredential.user;
    
    console.log(' Conversation-specific anonymous user created');
    return persistentConversationUser;
  } catch (error) {
    console.error(' Failed to create conversation authentication:', error);
    return null;
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

// Function to save conversation
export const saveConversation = async (
  messages: any[], 
  topicName?: string,
  initialTimestamp?: number
) => {
  try {
    // Ensure user is authenticated
    const conversationUser = auth.currentUser;
    if (!conversationUser) {
      throw new Error('User not authenticated');
    }

    // Validate messages
    if (!messages || messages.length === 0) {
      throw new Error('No messages to save');
    }

    // Determine the base topic ID (consistent across saves)
    const baseTopicId = `${conversationUser.uid}_${topicName || 'default'}`;

    // Reference to the conversation document
    const conversationRef = doc(conversationDb, 'aicoach_conversations', baseTopicId);

    // Get existing document
    const existingDoc = await getDoc(conversationRef);
    
    // Timestamp for this save operation
    const timestamp = Date.now();

    // Prepare conversation data
    const conversationData: any = {
      userId: conversationUser.uid,
      userEmail: conversationUser.email,
      userName: conversationUser.email,
      topicName: topicName || 'default',
      updatedAt: new Date().toISOString(),
      createdAt: existingDoc.exists() 
        ? (existingDoc.data()?.createdAt || new Date().toISOString())
        : new Date().toISOString(),
    };

    // Get existing messages or initialize empty array
    const existingMessages = existingDoc.exists() 
      ? (existingDoc.data()?.messages || []) 
      : [];

    // Determine messages to save
    let messagesToSave;
    if (messages.length <= 2) {
      // If 2 or fewer messages, save all of them
      messagesToSave = messages;
    } else {
      // Otherwise, take the last two messages
      messagesToSave = messages.slice(-2);
    }

    // Sanitize and filter unique messages
    const uniqueNewMessages = messagesToSave
      .map(sanitizeMessageForFirestore)
      .filter(newMsg => 
        !existingMessages.some(existMsg => 
          existMsg.text === newMsg.text && existMsg.timestamp === newMsg.timestamp
        )
      );

    // Append unique messages
    conversationData.messages = [
      ...existingMessages, 
      ...uniqueNewMessages
    ];

    // Ensure originalTimestamp is preserved or set
    conversationData.originalTimestamp = existingDoc.exists() 
      ? (existingDoc.data()?.originalTimestamp || timestamp)
      : timestamp;

    // Update message count
    conversationData.messageCount = conversationData.messages.length;

    try {
      // Overwrite the document with merged data
      await setDoc(conversationRef, conversationData, { merge: false });
      console.log(' Conversation saved successfully');
      console.log('Conversation ID:', baseTopicId);
      console.log('User ID:', conversationUser.uid);
      console.log('Total Messages:', conversationData.messages.length);
      console.log('Original Timestamp:', conversationData.originalTimestamp);
      
      return { 
        topicId: baseTopicId, 
        timestamp: conversationData.originalTimestamp
      };
    } catch (writeError) {
      console.error(' Write Operation Failed:', {
        errorName: writeError.name,
        errorMessage: writeError.message,
        errorCode: writeError.code,
        topicId: baseTopicId,
        timestamp: conversationData.originalTimestamp
      });
      throw writeError;
    }
  } catch (error) {
    console.error(' Error saving conversation:', error);
    throw error;
  }
};

// Function to retrieve conversation history
export const getConversationHistory = async (topicName?: string) => {
  try {
    // Log authentication state
    console.log('Current Auth State:', {
      currentUser: auth.currentUser ? {
        uid: auth.currentUser.uid,
        email: auth.currentUser.email,
        displayName: auth.currentUser.displayName
      } : null
    });

    // Ensure the user is authenticated
    if (!auth.currentUser) {
      console.warn('No authenticated user found');
      return [];
    }

    // Log query parameters
    console.log('Conversation History Query Parameters:', {
      userId: auth.currentUser.uid,
      topicName: topicName || 'ALL'
    });

    // Create a query to find conversations for the current user
    let conversationQuery;
    if (topicName) {
      // Query for conversations matching the topic name
      conversationQuery = query(
        collection(conversationDb, 'aicoach_conversations'),
        where('userId', '==', auth.currentUser.uid),
        where('topicName', '==', topicName)
      );
    } else {
      // If no topic specified, retrieve all conversations for the user
      conversationQuery = query(
        collection(conversationDb, 'aicoach_conversations'),
        where('userId', '==', auth.currentUser.uid)
      );
    }
    
    // Execute the query
    const querySnapshot = await getDocs(conversationQuery);
    
    // Log query results
    console.log('Query Snapshot Details:', {
      totalDocs: querySnapshot.docs.length,
      docIds: querySnapshot.docs.map(doc => doc.id)
    });

    // Map and return conversations, sorting by timestamp
    const conversations = querySnapshot.docs
      .map(doc => {
        const data = doc.data();
        console.log('Individual Conversation Log:', {
          id: doc.id,
          topicName: data.topicName,
          messageCount: data.messages?.length || 0,
          originalTimestamp: data.originalTimestamp,
          firstMessage: data.messages?.[0]?.text,
          lastMessage: data.messages?.[data.messages.length - 1]?.text
        });
        
        return { 
          id: doc.id, 
          ...data,
          messages: data.messages || [],
          originalTimestamp: data.originalTimestamp || Date.now()
        };
      })
      .sort((a, b) => b.originalTimestamp - a.originalTimestamp);

    console.log('Final Conversations Array:', {
      count: conversations.length,
      topicNames: conversations.map(c => c.topicName)
    });

    return conversations;
  } catch (error) {
    console.error('Detailed Error retrieving conversation history:', {
      errorName: error.name,
      errorMessage: error.message,
      errorCode: error.code,
      stack: error.stack
    });
    
    // Return an empty array instead of throwing an error
    return [];
  }
};

// Function to load a specific conversation by its ID
export const loadConversation = async (conversationId: string) => {
  try {
    // Ensure authentication
    const authToken = await ensureAuth(true);

    if (!auth.currentUser || !authToken) {
      throw new Error('Failed to authenticate');
    }

    // Reference to the specific conversation document
    const conversationRef = doc(conversationDb, 'aicoach_conversations', conversationId);
    const conversationDoc = await getDoc(conversationRef);

    // Check if the document exists and belongs to the current user
    if (!conversationDoc.exists()) {
      throw new Error('Conversation not found');
    }

    const conversationData = conversationDoc.data();
    
    // Verify the conversation belongs to the current user
    if (conversationData?.userId !== auth.currentUser.uid) {
      throw new Error('Unauthorized access to conversation');
    }

    return {
      id: conversationDoc.id,
      ...conversationData,
      messages: conversationData?.messages || [],
      originalTimestamp: conversationData?.originalTimestamp
    };
  } catch (error) {
    console.error('Error loading conversation:', error);
    throw error;
  }
};

// Function to delete a conversation
export const deleteConversation = async (conversationId: string) => {
  try {
    // Ensure authentication
    const authToken = await ensureAuth(true);

    if (!auth.currentUser || !authToken) {
      throw new Error('Failed to authenticate');
    }

    // Reference to the specific conversation document
    const conversationRef = doc(conversationDb, 'aicoach_conversations', conversationId);
    const conversationDoc = await getDoc(conversationRef);

    // Check if the document exists and belongs to the current user
    if (!conversationDoc.exists()) {
      throw new Error('Conversation not found');
    }

    const conversationData = conversationDoc.data();
    
    // Verify the conversation belongs to the current user
    if (conversationData?.userId !== auth.currentUser.uid) {
      throw new Error('Unauthorized access to conversation');
    }

    // Delete the conversation
    await deleteDoc(conversationRef);

    console.log('Conversation deleted successfully:', conversationId);
    return true;
  } catch (error) {
    console.error('Error deleting conversation:', error);
    throw error;
  }
};

// Enhanced retry mechanism for network-related errors
const retryOperation = async <T>(
  operation: () => Promise<T>, 
  maxRetries = 3, 
  delay = 1000
): Promise<T> => {
  let lastError: Error | null = null;

  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      return await operation();
    } catch (error) {
      lastError = error as Error;
      
      console.warn(`Attempt ${attempt} failed:`, error);

      // Wait before retrying
      await new Promise(resolve => setTimeout(resolve, delay * attempt));
    }
  }

  console.error('All retry attempts failed:', lastError);
  throw lastError;
};

// Export the main app's auth and db
export { db, auth };
