import {
  Injectable,
  Logger,
  BadGatewayException,
  ServiceUnavailableException,
  BadRequestException,
} from '@nestjs/common';
import { HttpService } from '@nestjs/axios';
import { ConfigService } from '@nestjs/config';
import { firstValueFrom } from 'rxjs';
import { AxiosError } from 'axios';
import { GenerateContentDto, SimilarContentDto } from './content.dto';

@Injectable()
export class ContentService {
  private readonly logger = new Logger(ContentService.name);

  constructor(
    private readonly http: HttpService,
    private readonly config: ConfigService,
  ) {}

  private get backendUrl(): string {
    return this.config.get<string>('backendUrl')!;
  }

  async generate(dto: GenerateContentDto) {
    this.logger.log(
      `Generating content — platform=${dto.platform}, goal=${dto.goal}`,
    );
    try {
      const { data } = await firstValueFrom(
        this.http.post(`${this.backendUrl}/api/v1/content/generate`, dto),
      );
      return data;
    } catch (err) {
      this.handleBackendError(err, 'content generation');
    }
  }

  async findSimilar(dto: SimilarContentDto) {
    const topK = dto.top_k ?? 5;
    this.logger.log(`Searching similar content — query="${dto.query}", top_k=${topK}`);
    try {
      const { data } = await firstValueFrom(
        this.http.post(`${this.backendUrl}/api/v1/content/similar`, {
          query: dto.query,
          top_k: topK,
        }),
      );
      return data;
    } catch (err) {
      this.handleBackendError(err, 'similar content search');
    }
  }

  async health() {
    this.logger.log('Checking backend health');
    try {
      const { data } = await firstValueFrom(
        this.http.get(`${this.backendUrl}/api/v1/content/health`),
      );
      return data;
    } catch (err) {
      this.handleBackendError(err, 'health check');
    }
  }

  /**
   * Translates Axios / HTTP errors from the FastAPI backend into appropriate
   * NestJS HTTP exceptions so the BFF returns meaningful status codes.
   */
  private handleBackendError(err: unknown, operation: string): never {
    const axiosErr = err as AxiosError;
    if (axiosErr.response) {
      const status = axiosErr.response.status;
      const detail =
        (axiosErr.response.data as any)?.detail ??
        `Backend ${operation} failed`;
      this.logger.error(
        `Backend returned ${status} for ${operation}: ${JSON.stringify(axiosErr.response.data)}`,
      );
      if (status >= 400 && status < 500) {
        throw new BadRequestException(detail);
      }
      throw new BadGatewayException(detail);
    }
    // Network-level error (ECONNREFUSED, timeout, etc.)
    this.logger.error(`Backend unreachable during ${operation}: ${axiosErr.message}`);
    throw new ServiceUnavailableException(
      `Backend service is unavailable (${operation})`,
    );
  }
}
