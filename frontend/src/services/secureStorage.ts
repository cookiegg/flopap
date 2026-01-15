/**
 * 安全存储服务 - 使用Web Crypto API加密API密钥
 */

class SecureStorage {
  private static readonly STORAGE_KEY = 'encrypted_api_keys';
  private static readonly SALT_KEY = 'storage_salt';
  
  private static async getKey(): Promise<CryptoKey> {
    let salt = localStorage.getItem(this.SALT_KEY);
    if (!salt) {
      const saltArray = crypto.getRandomValues(new Uint8Array(16));
      salt = Array.from(saltArray).map(b => b.toString(16).padStart(2, '0')).join('');
      localStorage.setItem(this.SALT_KEY, salt);
    }
    
    const keyMaterial = await crypto.subtle.importKey(
      'raw',
      new TextEncoder().encode(salt + 'flopap_secure_key'),
      { name: 'PBKDF2' },
      false,
      ['deriveKey']
    );
    
    return crypto.subtle.deriveKey(
      {
        name: 'PBKDF2',
        salt: new TextEncoder().encode(salt),
        iterations: 100000,
        hash: 'SHA-256'
      },
      keyMaterial,
      { name: 'AES-GCM', length: 256 },
      false,
      ['encrypt', 'decrypt']
    );
  }
  
  static async setItem(key: string, value: string): Promise<void> {
    try {
      const cryptoKey = await this.getKey();
      const iv = crypto.getRandomValues(new Uint8Array(12));
      const encodedValue = new TextEncoder().encode(value);
      
      const encrypted = await crypto.subtle.encrypt(
        { name: 'AES-GCM', iv },
        cryptoKey,
        encodedValue
      );
      
      const encryptedData = {
        iv: Array.from(iv),
        data: Array.from(new Uint8Array(encrypted))
      };
      
      const existingData = this.getAllEncrypted();
      existingData[key] = encryptedData;
      localStorage.setItem(this.STORAGE_KEY, JSON.stringify(existingData));
    } catch (error) {
      console.error('Failed to encrypt and store data:', error);
      throw new Error('Storage encryption failed');
    }
  }
  
  static async getItem(key: string): Promise<string | null> {
    try {
      const allData = this.getAllEncrypted();
      const encryptedData = allData[key];
      
      if (!encryptedData) return null;
      
      const cryptoKey = await this.getKey();
      const iv = new Uint8Array(encryptedData.iv);
      const data = new Uint8Array(encryptedData.data);
      
      const decrypted = await crypto.subtle.decrypt(
        { name: 'AES-GCM', iv },
        cryptoKey,
        data
      );
      
      return new TextDecoder().decode(decrypted);
    } catch (error) {
      console.error('Failed to decrypt data:', error);
      return null;
    }
  }
  
  static removeItem(key: string): void {
    const allData = this.getAllEncrypted();
    delete allData[key];
    localStorage.setItem(this.STORAGE_KEY, JSON.stringify(allData));
  }
  
  static clear(): void {
    localStorage.removeItem(this.STORAGE_KEY);
    localStorage.removeItem(this.SALT_KEY);
  }
  
  private static getAllEncrypted(): Record<string, any> {
    const stored = localStorage.getItem(this.STORAGE_KEY);
    return stored ? JSON.parse(stored) : {};
  }
}

export default SecureStorage;
