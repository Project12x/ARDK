import { Octokit } from '@octokit/rest';

export interface GitHubUser {
    login: string;
    avatar_url: string;
    html_url: string;
}

export interface GitHubRepo {
    id: number;
    name: string;
    full_name: string;
    html_url: string;
    private: boolean;
    description: string | null;
}

class GitHubServiceImpl {
    private octokit: Octokit | null = null;
    private _isAuthenticated = false;

    constructor() {
        const token = localStorage.getItem('GITHUB_TOKEN');
        if (token) {
            this.initialize(token);
        }
    }

    initialize(token: string) {
        this.octokit = new Octokit({ auth: token });
        this._isAuthenticated = true;
    }

    get isAuthenticated() {
        return this._isAuthenticated;
    }

    logout() {
        this.octokit = null;
        this._isAuthenticated = false;
        localStorage.removeItem('GITHUB_TOKEN');
    }

    async verifyToken(token: string): Promise<GitHubUser | null> {
        try {
            const tempKit = new Octokit({ auth: token });
            const { data } = await tempKit.users.getAuthenticated();

            // If successful, save and initialize
            localStorage.setItem('GITHUB_TOKEN', token);
            this.initialize(token);

            return {
                login: data.login,
                avatar_url: data.avatar_url,
                html_url: data.html_url
            };
        } catch (error) {
            console.error('GitHub Token Verification Failed:', error);
            return null;
        }
    }

    async getUser(): Promise<GitHubUser | null> {
        if (!this.octokit) return null;
        try {
            const { data } = await this.octokit.users.getAuthenticated();
            return {
                login: data.login,
                avatar_url: data.avatar_url,
                html_url: data.html_url
            };
        } catch (error) {
            console.error(error);
            return null;
        }
    }

    async getRepos(): Promise<GitHubRepo[]> {
        if (!this.octokit) return [];
        try {
            const { data } = await this.octokit.repos.listForAuthenticatedUser({
                sort: 'updated',
                per_page: 100
            });
            return data.map((repo: any) => ({
                id: repo.id,
                name: repo.name,
                full_name: repo.full_name,
                html_url: repo.html_url,
                private: repo.private,
                description: repo.description
            }));
        } catch (error) {
            console.error("Failed to fetch repos", error);
            return [];
        }
    }
}

export const GitHubService = new GitHubServiceImpl();
